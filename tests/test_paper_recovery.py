"""Ways out of a stopped paper plan, lookups that a resumed plan skips, and refusals that name the stock.
All symbols and values are fictional."""
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from conftest import AT, FakeBroker
from public_pilot import cli
from public_pilot.broker import BrokerRefused
from public_pilot.common import Refused, iso, loads, now
from public_pilot.execution import NEVER_PLACED, REFUSED, SETTLE_SECONDS, cancel, client_id, execute
from public_pilot.planning import Limits, build_plan
from public_pilot.state import Store
from support import call, write

ROOT = Path(__file__).resolve().parents[1]
SETTLED = AT + timedelta(seconds=Limits().plan_max_age_seconds + SETTLE_SECONDS)


def run(store, identity, broker, trust, at=AT):
    return execute(store, identity, broker, trust, clock=lambda: at)


class Refusing(FakeBroker):
    """Refuses one submission outright, as the broker does for insufficient buying power."""

    def __init__(self, snapshot, refuse_at):
        super().__init__(snapshot)
        self.refuse_at = refuse_at

    def submit(self, order):
        if self.posts + 1 == self.refuse_at:
            self.posts += 1
            raise BrokerRefused("Broker returned HTTP 403: insufficient buying power; no automatic submission retry",
                                403, "insufficient buying power")
        return super().submit(order)


class Counting(FakeBroker):
    def __init__(self, snapshot):
        super().__init__(snapshot)
        self.looked_up = []

    def lookup(self, coid):
        self.looked_up.append(coid)
        return super().lookup(coid)


def test_a_refused_submission_halts_the_plan_and_a_fresh_plan_trades_the_rest(store, author, payload, snapshot):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    identity = store.save_plan(build_plan(payload, snapshot, Limits(), AT))
    assert [o["symbol"] for o in store.plan(identity)[0]["orders"]] == ["DEMOA", "DEMOA", "DEMOB", "DEMOB"]
    broker = Refusing(snapshot, refuse_at=3)
    result = run(store, identity, broker, trust)
    assert result == {"plan_id": identity, "status": "halted", "order_status": REFUSED, "symbol": "DEMOB",
                      "reason": "Broker returned HTTP 403: insufficient buying power; no automatic submission retry",
                      "next_step": "Inspect fills and create a fresh preview"}
    record = store.order(identity, 2)
    assert record["attempted"] == 1 and loads(record["observation"]) == {
        "client_order_id": client_id(identity, 2), "symbol": "DEMOB", "status": REFUSED, "http_status": 403,
        "detail": "insufficient buying power"}
    assert not store.outstanding()
    assert run(store, identity, broker, trust) == {"plan_id": identity, "status": "halted"}
    assert cancel(store, identity, broker) == {"plan_id": identity, "status": "halted"}
    assert broker.posts == 3
    later = AT + timedelta(seconds=1)
    fresh = store.save_plan(build_plan(payload, broker.snapshot(None), Limits(), later))
    assert run(store, fresh, broker, trust, at=later)["status"] == "complete"
    assert broker.data["positions"] == {"DEMOA": "3", "DEMOB": "3"} and broker.posts == 5


def test_an_unanswered_submission_is_never_resent_and_cancel_closes_the_plan_once_settled(store, prepared, author):
    identity, broker = prepared
    broker.lose_response = True
    broker.accept_before_loss = False
    with pytest.raises(Refused, match="lost"):
        run(store, identity, broker, author[0])
    with pytest.raises(Refused, match="^DEMOA: Submission outcome is uncertain; no retry") as uncertain:
        run(store, identity, broker, author[0])
    assert f"From {iso(SETTLED)}, cancel-paper closes this plan" in str(uncertain.value)
    with pytest.raises(Refused, match="^DEMOA: Cannot cancel an uncertain submission yet") as early:
        cancel(store, identity, broker, clock=lambda: SETTLED - timedelta(seconds=1))
    assert f"again from {iso(SETTLED)}" in str(early.value)
    assert store.outstanding()
    assert cancel(store, identity, broker, clock=lambda: SETTLED) == {
        "plan_id": identity, "status": "canceled",
        "never_placed": [{"symbol": "DEMOA", "client_order_id": client_id(identity, 0)}]}
    assert loads(store.order(identity, 0)["observation"])["status"] == NEVER_PLACED
    assert not store.outstanding()
    assert run(store, identity, broker, author[0]) == {"plan_id": identity, "status": "canceled"}
    assert broker.posts == 1 and not broker.orders


def test_an_unanswered_submission_that_reached_the_broker_is_cancelled_normally(store, prepared, author):
    identity, broker = prepared
    broker.fill_on_submit = False
    broker.lose_response = True  # the broker accepts the order, then the response is lost
    with pytest.raises(Refused, match="lost"):
        run(store, identity, broker, author[0])
    assert cancel(store, identity, broker, clock=lambda: AT) == {"plan_id": identity, "status": "canceled"}
    assert [o["status"] for o in broker.orders.values()] == ["canceled"]


def test_an_order_the_broker_reported_and_then_lost_is_never_written_off(store, prepared, author):
    identity, broker = prepared
    broker.fill_on_submit = False
    assert run(store, identity, broker, author[0])["status"] == "pending"
    broker.orders.clear()
    with pytest.raises(Refused, match="^DEMOA: The broker no longer finds an order it reported"):
        cancel(store, identity, broker, clock=lambda: AT + timedelta(days=1))
    assert store.outstanding()


def test_a_resumed_plan_does_not_look_up_orders_already_filled(store, author, payload, snapshot):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    identity = store.save_plan(build_plan(payload, snapshot, Limits(), AT))
    broker = Counting(snapshot)
    broker.fill_on_submit = False
    first, second, third = (client_id(identity, i) for i in range(3))
    assert run(store, identity, broker, trust)["status"] == "pending"
    broker.fill(first)
    assert run(store, identity, broker, trust)["status"] == "pending"
    broker.fill(second)
    broker.looked_up.clear()
    assert run(store, identity, broker, trust) == {
        "plan_id": identity, "status": "pending", "client_order_id": third, "symbol": "DEMOB",
        "next_step": "Run execute again to reconcile, or cancel this plan"}
    assert broker.looked_up == [second, third, third]  # the first order's fill is final


def test_cancelling_looks_up_only_unfinished_orders(store, author, payload, snapshot):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    identity = store.save_plan(build_plan(payload, snapshot, Limits(), AT))
    broker = Counting(snapshot)
    broker.fill_on_submit = False
    first, second = client_id(identity, 0), client_id(identity, 1)
    run(store, identity, broker, trust)
    broker.fill(first)
    assert run(store, identity, broker, trust)["status"] == "pending"
    broker.looked_up.clear()
    assert cancel(store, identity, broker) == {"plan_id": identity, "status": "canceled"}
    assert broker.looked_up == [second, second]  # before and after cancelling it


def quoted(symbol, bid, ask):
    return lambda s: s["quotes"][symbol].update(bid=bid, ask=ask)


@pytest.mark.parametrize("change, limits, message", [
    (lambda s: s["quotes"].pop("DEMOB"), Limits(), "^DEMOB: Missing quote$"),
    (quoted("DEMOA", "90", "100"), Limits(), "^DEMOA: Quote spread exceeds limit$"),
    (quoted("DEMOB", "100", "99"), Limits(), "^DEMOB: Invalid or crossed quote$"),
    (lambda s: s["quotes"]["DEMOB"].update(at=iso(AT - timedelta(minutes=3))), Limits(),
     "^DEMOB: Stale or future quote$"),
    (lambda s: s["assets"]["DEMOB"].update(tradable=False), Limits(), "^DEMOB: Asset is not tradable$"),
    (lambda s: s.update(positions={"DEMOA": "1", "DEMOZ": "1"}), Limits(),
     "^Foreign positions outside this research universe: DEMOZ$"),
    (lambda s: s.update(positions={"DEMOB": "-2"}), Limits(), "^DEMOB: Only long, whole-share positions"),
    (lambda s: s.update(open_orders=[{"id": "outside-order", "symbol": "DEMOB"}]), Limits(),
     "^Resolve existing broker orders before planning: DEMOB$"),
    (lambda s: None, Limits(max_position_weight="0.3"),
     "^Research exceeds the customer's concentration limit: DEMOA, DEMOB$"),
    (quoted("DEMOA", "299.9", "300"), Limits(),
     r"^DEMOA: One share exceeds the per-order limit \(limit price 300.75 USD, per-order limit 250 USD\)$"),
])
def test_planning_refusals_name_the_stock(payload, snapshot, change, limits, message):
    change(snapshot)
    with pytest.raises(Refused, match=message):
        build_plan(payload, snapshot, limits, AT)


def test_execution_refusals_name_the_stock(store, prepared, author):
    identity, broker = prepared
    broker.data["quotes"]["DEMOA"].update(bid="101.9", ask="102")
    with pytest.raises(Refused, match="^DEMOA: Quote moved beyond the limit or observed cash is insufficient$"):
        run(store, identity, broker, author[0])
    broker.data["quotes"]["DEMOA"].update(bid="99.9", ask="100")
    broker.data["positions"] = {"DEMOB": "1"}
    with pytest.raises(Refused, match=r"^Positions changed outside this plan \(DEMOB\); stop and reconcile$"):
        run(store, identity, broker, author[0])
    broker.data["positions"] = {}
    broker.orders["outside"] = {"symbol": "DEMOB", "status": "accepted"}
    with pytest.raises(Refused, match="^An open broker order blocks the next submission: DEMOB$"):
        run(store, identity, broker, author[0])
    assert broker.posts == 0


def current_edition(tmp_path, author, payload, capsys):
    """A current edition installed from the command line; returns the global arguments for that state."""
    trust, sign = author
    started = now()
    payload.update(published_at=iso(started - timedelta(days=1)), information_cutoff=iso(started - timedelta(days=2)),
                   valid_until=iso(started + timedelta(days=30)))
    args = ["--state", tmp_path / "state", "--trust", write(tmp_path / "trust.json", trust)]
    assert call(capsys, args + ["install", write(tmp_path / "edition.json", sign(payload))])[0] == 0
    return args


def account_fixture(tmp_path, ask, cash="5000"):
    bid = str(Decimal(ask) - Decimal("0.1"))
    return write(tmp_path / f"account-{ask}.json", {
        "account_id": "paper-test-account", "cash": cash, "equity": cash, "positions": {},
        "observed_at": iso(AT), "market_open": True, "open_orders": [],
        "quotes": {s: {"bid": bid, "ask": ask, "at": iso(AT)} for s in ("DEMOA", "DEMOB")},
        "assets": {s: {"tradable": True} for s in ("DEMOA", "DEMOB")}})


def test_the_command_line_buys_shares_priced_up_to_its_default_order_limit(tmp_path, author, payload, capsys):
    assert cli.parser().parse_args(["preview", "test-research"]).max_order == cli.DEFAULT_MAX_ORDER == "1000"
    assert f"\nPILOT_MAX_ORDER={cli.DEFAULT_MAX_ORDER}\n" in (ROOT / "examples" / "paper.env.example").read_text()
    args = current_edition(tmp_path, author, payload, capsys)
    sized = ["--allocation", "5000", "--max-turnover", "5000"]
    code, preview = call(capsys, args + ["preview", "test-research", "--offline", account_fixture(tmp_path, "900")]
                         + sized)
    assert code == 0
    assert [(o["symbol"], o["qty"], o["limit_price"]) for o in preview["plan"]["orders"]] == [
        ("DEMOA", "1", "902.25"), ("DEMOA", "1", "902.25"), ("DEMOB", "1", "902.25"), ("DEMOB", "1", "902.25")]
    code, refusal = call(capsys, args + ["preview", "test-research", "--offline", account_fixture(tmp_path, "1000")]
                         + sized)
    assert code == 2 and refusal["reason"] == (
        "DEMOA: One share exceeds the per-order limit (limit price 1002.50 USD, per-order limit 1000 USD)")


def test_a_preview_blocked_by_an_unresolved_plan_names_that_plan(tmp_path, author, payload, capsys):
    args = current_edition(tmp_path, author, payload, capsys)
    store = Store(tmp_path / "state")
    try:
        store.db.execute("INSERT INTO plans VALUES ('unresolved-plan','{}','started')")
    finally:
        store.close()
    code, refusal = call(capsys, args + ["preview", "test-research", "--offline", account_fixture(tmp_path, "100")])
    assert code == 2
    assert refusal["reason"] == "Reconcile or cancel the outstanding execution first: plan unresolved-plan"
