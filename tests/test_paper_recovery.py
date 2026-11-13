"""Ways out of a stopped paper plan, the broker answers that are kept, lookups that a resumed plan skips, and
refusals that name the stock. All symbols and values are fictional."""
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from conftest import AT, FakeBroker
from public_pilot import cli
from public_pilot.broker import OrderRejected
from public_pilot.common import Refused, iso, loads, now
from public_pilot.execution import REJECTED, cancel, client_id, execute
from public_pilot.planning import Limits, build_plan
from public_pilot.state import Store
from support import call, write

ROOT = Path(__file__).resolve().parents[1]
UNCERTAIN = "^DEMOA: Submission outcome is uncertain; no retry. Inspect broker history manually$"
REPORTED = "^DEMOA: The broker no longer finds an order it reported; inspect broker history manually$"


def run(store, identity, broker, trust, at=AT):
    return execute(store, identity, broker, trust, clock=lambda: at)


def planned(store, author, payload, snapshot):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    return store.save_plan(build_plan(payload, snapshot, Limits(), AT))


class Broker(FakeBroker):
    """The shared simulated broker, plus a lookup by the broker's own order ID."""

    def order(self, broker_id):
        return deepcopy(next((o for o in self.orders.values() if o["id"] == broker_id), None))


class ClientIdBlind(Broker):
    """Answers a lookup by client order ID with nothing once the order exists, but finds it by the broker's ID."""

    def lookup(self, coid):
        return None if coid in self.orders else super().lookup(coid)


class Rejecting(Broker):
    """Rejects one submission outright, as the broker does for insufficient buying power."""

    def __init__(self, snapshot, reject_at):
        super().__init__(snapshot)
        self.reject_at = reject_at

    def submit(self, order):
        if self.posts + 1 == self.reject_at:
            self.posts += 1
            raise OrderRejected("Broker returned HTTP 403: insufficient buying power; no automatic submission retry",
                                403, "insufficient buying power")
        return super().submit(order)


class Hiding(Broker):
    """Accepts orders but shows them to no lookup yet, or fails to answer lookups at all."""

    def __init__(self, snapshot, failure):
        super().__init__(snapshot)
        self.failure = failure
        self.fill_on_submit = False

    def hidden(self):
        if self.failure == "error":
            raise Refused("Broker transport failed; any attempted submission requires reconciliation")

    def lookup(self, coid):
        return self.hidden() if self.failure and coid in self.orders else super().lookup(coid)

    def order(self, broker_id):
        return self.hidden() if self.failure else super().order(broker_id)


class Counting(Broker):
    def __init__(self, snapshot):
        super().__init__(snapshot)
        self.looked_up = []

    def lookup(self, coid):
        self.looked_up.append(coid)
        return super().lookup(coid)


class CancelFails(Broker):
    def cancel(self, broker_id):
        raise Refused("Broker transport failed; any attempted submission requires reconciliation")


def test_a_rejected_submission_halts_the_plan_and_a_fresh_plan_trades_the_rest(store, author, payload, snapshot):
    trust = author[0]
    identity = planned(store, author, payload, snapshot)
    assert [o["symbol"] for o in store.plan(identity)[0]["orders"]] == ["DEMOA", "DEMOA", "DEMOB", "DEMOB"]
    broker = Rejecting(snapshot, reject_at=3)
    assert run(store, identity, broker, trust) == {
        "plan_id": identity, "status": "halted", "order_status": REJECTED, "symbol": "DEMOB",
        "reason": "Broker returned HTTP 403: insufficient buying power; no automatic submission retry",
        "next_step": "Inspect fills and create a fresh preview"}
    record = store.order(identity, 2)
    assert record["attempted"] == 1 and loads(record["observation"]) == {
        "client_order_id": client_id(identity, 2), "symbol": "DEMOB", "status": REJECTED, "http_status": 403,
        "detail": "insufficient buying power"}
    assert not store.outstanding()
    assert run(store, identity, broker, trust) == {"plan_id": identity, "status": "halted"}
    assert cancel(store, identity, broker) == {"plan_id": identity, "status": "halted"}
    assert broker.posts == 3
    later = AT + timedelta(seconds=1)
    fresh = store.save_plan(build_plan(payload, broker.snapshot(None), Limits(), later))
    assert run(store, fresh, broker, trust, at=later)["status"] == "complete"
    assert broker.data["positions"] == {"DEMOA": "3", "DEMOB": "3"} and broker.posts == 5


def test_an_unanswered_submission_is_resolved_only_by_the_broker(store, prepared, author):
    identity, broker = prepared
    broker.lose_response = True
    broker.accept_before_loss = False
    with pytest.raises(Refused, match="lost"):
        run(store, identity, broker, author[0])
    # However much later, a lookup miss is not proof that no order was created.
    with pytest.raises(Refused, match=UNCERTAIN):
        run(store, identity, broker, author[0], at=AT + timedelta(days=30))
    with pytest.raises(Refused, match=UNCERTAIN):
        cancel(store, identity, broker)
    assert store.outstanding() and broker.posts == 1
    coid = client_id(identity, 0)
    broker.orders[coid] = {**store.plan(identity)[0]["orders"][0], "client_order_id": coid, "id": "broker-late",
                           "status": "accepted", "filled_qty": "0", "filled_avg_price": None}
    assert cancel(store, identity, broker) == {"plan_id": identity, "status": "canceled"}
    assert broker.orders[coid]["status"] == "canceled" and broker.posts == 1


@pytest.mark.parametrize("failure", ["hidden", "error"])
def test_the_brokers_acceptance_is_kept_before_the_lookup(store, author, payload, snapshot, failure):
    trust = author[0]
    identity = planned(store, author, payload, snapshot)
    broker = Hiding(snapshot, failure)
    coid = client_id(identity, 0)
    if failure == "hidden":
        assert run(store, identity, broker, trust)["status"] == "pending"
    else:
        with pytest.raises(Refused, match="transport failed"):
            run(store, identity, broker, trust)
    kept = loads(store.order(identity, 0)["observation"])
    assert (kept["id"], kept["status"]) == ("broker-" + coid, "accepted")
    if failure == "hidden":
        with pytest.raises(Refused, match=REPORTED):
            run(store, identity, broker, trust)
        with pytest.raises(Refused, match=REPORTED):
            cancel(store, identity, broker)
    assert store.outstanding() and broker.posts == 1
    broker.failure = None
    assert cancel(store, identity, broker) == {"plan_id": identity, "status": "canceled"}
    assert broker.posts == 1


def test_a_reported_order_is_kept_before_the_cancellation_request(store, author, payload, snapshot):
    identity = planned(store, author, payload, snapshot)
    broker = CancelFails(snapshot)
    broker.fill_on_submit = False
    assert run(store, identity, broker, author[0])["status"] == "pending"
    order = broker.orders[client_id(identity, 0)]
    order.update(status="partially_filled", filled_qty="1", filled_avg_price=order["limit_price"])
    with pytest.raises(Refused, match="transport failed"):
        cancel(store, identity, broker)
    kept = loads(store.order(identity, 0)["observation"])
    assert (kept["status"], kept["filled_qty"]) == ("partially_filled", "1")


def test_an_unanswered_submission_that_reached_the_broker_is_cancelled_normally(store, prepared, author):
    identity, broker = prepared
    broker.fill_on_submit = False
    broker.lose_response = True  # the broker accepts the order, then the response is lost
    with pytest.raises(Refused, match="lost"):
        run(store, identity, broker, author[0])
    assert cancel(store, identity, broker) == {"plan_id": identity, "status": "canceled"}
    assert [o["status"] for o in broker.orders.values()] == ["canceled"]


def test_an_order_the_broker_reported_and_then_lost_is_never_written_off(store, author, payload, snapshot):
    identity = planned(store, author, payload, snapshot)
    broker = Broker(snapshot)
    broker.fill_on_submit = False
    assert run(store, identity, broker, author[0])["status"] == "pending"
    broker.orders.clear()  # gone by client order ID and by the broker's own ID
    with pytest.raises(Refused, match=REPORTED):
        run(store, identity, broker, author[0], at=AT + timedelta(days=1))
    with pytest.raises(Refused, match=REPORTED):
        cancel(store, identity, broker)
    assert store.outstanding()


def test_the_saved_broker_order_id_finds_an_order_that_a_client_id_lookup_misses(store, author, payload, snapshot):
    trust = author[0]
    identity = planned(store, author, payload, snapshot)
    broker = ClientIdBlind(snapshot)
    broker.fill_on_submit = False
    first = client_id(identity, 0)
    assert run(store, identity, broker, trust)["status"] == "pending"
    broker.fill(first)
    assert run(store, identity, broker, trust)["status"] == "pending"  # the first order is filled; the next is sent
    assert loads(store.order(identity, 0)["observation"])["status"] == "filled"
    broker.orders[client_id(identity, 1)]["status"] = "canceled"
    assert run(store, identity, broker, trust) == {
        "plan_id": identity, "status": "halted", "order_status": "canceled", "symbol": "DEMOA",
        "next_step": "Inspect fills and create a fresh preview"}
    assert not store.outstanding() and broker.posts == 2


def test_cancel_finds_an_order_by_its_saved_broker_order_id(store, author, payload, snapshot):
    identity = planned(store, author, payload, snapshot)
    broker = ClientIdBlind(snapshot)
    broker.fill_on_submit = False
    assert run(store, identity, broker, author[0])["status"] == "pending"
    assert cancel(store, identity, broker) == {"plan_id": identity, "status": "canceled"}
    assert broker.orders[client_id(identity, 0)]["status"] == "canceled"
    assert loads(store.order(identity, 0)["observation"])["status"] == "canceled"


def test_an_order_found_by_its_broker_order_id_is_validated_before_it_is_recorded(store, author, payload, snapshot):
    identity = planned(store, author, payload, snapshot)
    broker = ClientIdBlind(snapshot)
    broker.fill_on_submit = False
    assert run(store, identity, broker, author[0])["status"] == "pending"
    kept = loads(store.order(identity, 0)["observation"])
    broker.orders[client_id(identity, 0)]["client_order_id"] = "another-client-order"
    with pytest.raises(Refused, match="^DEMOA: Broker order identity mismatch$"):
        run(store, identity, broker, author[0])
    with pytest.raises(Refused, match="^DEMOA: Broker order identity mismatch$"):
        cancel(store, identity, broker)
    assert loads(store.order(identity, 0)["observation"]) == kept and store.outstanding()


def test_a_resumed_plan_does_not_look_up_orders_already_filled(store, author, payload, snapshot):
    trust = author[0]
    identity = planned(store, author, payload, snapshot)
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
    trust = author[0]
    identity = planned(store, author, payload, snapshot)
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
