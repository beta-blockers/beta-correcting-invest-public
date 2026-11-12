from datetime import timedelta

import pytest

from conftest import AT, FakeBroker
from public_pilot.common import Refused, digest
from public_pilot.execution import cancel, execute, validate_observation
from public_pilot.planning import Limits, build_plan
from public_pilot.state import Store


def run(store, identity, broker, trust):
    return execute(store, identity, broker, trust, clock=lambda: AT)


def test_execution_is_repeatable_without_duplicate_submissions(store, prepared, author):
    identity, broker = prepared
    assert run(store, identity, broker, author[0])["status"] == "complete"
    count = broker.posts
    assert count > 0
    assert run(store, identity, broker, author[0])["status"] == "complete"
    assert broker.posts == count


def test_crash_after_acceptance_recovers_after_reopening_database(store, prepared, author):
    identity, broker = prepared
    broker.lose_response = True
    with pytest.raises(Refused, match="lost"):
        run(store, identity, broker, author[0])
    reopened = Store(store.directory)
    try:
        assert run(reopened, identity, broker, author[0])["status"] == "complete"
        assert broker.posts == len(reopened.plan(identity)[0]["orders"])
    finally:
        reopened.close()


def test_unknown_submission_is_never_retried(store, prepared, author):
    identity, broker = prepared
    broker.lose_response = True
    broker.accept_before_loss = False
    with pytest.raises(Refused):
        run(store, identity, broker, author[0])
    with pytest.raises(Refused, match="uncertain"):
        run(store, identity, broker, author[0])
    assert broker.posts == 1
    assert store.outstanding()


def test_unfilled_sell_blocks_buys_and_cancel_reconciles(store, author, payload, snapshot):
    trust, sign = author
    snapshot.update(cash="100", positions={"DEMOA": "9"})
    payload["targets"] = {"DEMOB": "0.4"}
    store.install(sign(payload), trust, AT)
    identity = store.save_plan(build_plan(payload, snapshot, Limits(max_turnover_usd="1500"), AT))
    broker = FakeBroker(snapshot)
    broker.fill_on_submit = False
    assert run(store, identity, broker, trust)["status"] == "pending"
    assert all(o["side"] == "sell" for o in broker.orders.values())
    assert cancel(store, identity, broker)["status"] == "canceled"
    assert not store.outstanding()


@pytest.mark.parametrize("change", [
    {"account_id": "another-account"}, {"cash": "0"}, {"positions": {"DEMOA": "1"}},
])
def test_changed_account_state_prevents_submissions(store, prepared, author, change):
    identity, broker = prepared
    broker.data.update(change)
    with pytest.raises(Refused):
        run(store, identity, broker, author[0])
    assert broker.posts == 0


def test_expired_plan_cannot_submit_but_can_cancel(store, prepared, author):
    identity, broker = prepared
    with pytest.raises(Refused, match="expired"):
        execute(store, identity, broker, author[0], clock=lambda: AT + timedelta(minutes=10))
    assert broker.posts == 0
    assert cancel(store, identity, broker)["status"] == "canceled"


def test_offline_and_demo_packages_cannot_execute(store, author, payload, snapshot):
    trust, sign = author
    payload["purpose"] = "demo"
    store.install(sign(payload), trust, AT)
    broker = FakeBroker(snapshot)
    for offline in (True, False):
        identity = store.save_plan(build_plan(payload, snapshot, Limits(), AT, offline=offline))
        with pytest.raises(Refused):
            run(store, identity, broker, trust)
    assert broker.posts == 0


def test_another_unresolved_plan_blocks_execution(store, prepared, author):
    identity, broker = prepared
    store.db.execute("INSERT INTO plans VALUES ('other','{}','started')")
    with pytest.raises(Refused, match="Another plan"):
        run(store, identity, broker, author[0])
    assert broker.posts == 0


def test_broker_replacement_or_bad_fill_is_not_treated_as_success(store, prepared, author):
    identity, broker = prepared
    broker.fill_on_submit = False
    run(store, identity, broker, author[0])
    order = next(iter(broker.orders.values()))
    order["status"] = "replaced"
    with pytest.raises(Refused, match="replaced"):
        run(store, identity, broker, author[0])
    assert broker.posts == 1


def test_price_move_above_limit_prevents_buy(store, prepared, author):
    identity, broker = prepared
    broker.data["quotes"]["DEMOA"].update(bid="101.9", ask="102")
    with pytest.raises(Refused, match="Quote moved"):
        run(store, identity, broker, author[0])
    assert broker.posts == 0


def test_partial_fill_blocks_following_orders(store, prepared, author):
    identity, broker = prepared
    broker.fill_on_submit = False
    run(store, identity, broker, author[0])
    order = next(iter(broker.orders.values()))
    order.update(status="partially_filled", filled_qty="1", filled_avg_price=order["limit_price"])
    assert run(store, identity, broker, author[0])["status"] == "pending"
    assert broker.posts == 1


def test_impossible_fill_is_refused(store, prepared, author):
    identity, broker = prepared
    broker.fill_on_submit = False
    run(store, identity, broker, author[0])
    order = next(iter(broker.orders.values()))
    order.update(status="filled", filled_qty=order["qty"], filled_avg_price="999")
    with pytest.raises(Refused, match="limit price"):
        run(store, identity, broker, author[0])
    assert broker.posts == 1


def test_new_edition_blocks_remaining_submissions(store, prepared, author, payload):
    from conftest import delta_for
    from public_pilot.common import iso

    identity, broker = prepared
    broker.fill_on_submit = False
    run(store, identity, broker, author[0])
    broker.fill(next(iter(broker.orders)))
    delta = delta_for(payload, edition_id="edition-2", published_at=iso(AT - timedelta(days=1)))
    store.install(author[1](delta, "delta"), author[0], AT)
    with pytest.raises(Refused, match="Research changed"):
        run(store, identity, broker, author[0])
    assert broker.posts == 1
