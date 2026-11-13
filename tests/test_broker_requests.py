"""How many requests the paper broker client makes, what it reads before each order, and how it classifies refused
submissions. A simulated venue answers every request; all symbols and values are fictional."""
from datetime import timedelta
from decimal import Decimal
import json

import httpx
import pytest

from public_pilot import cli
from public_pilot.broker import AlpacaPaper, BrokerRefused, OrderRejected
from public_pilot.common import Refused, iso, now
from public_pilot.execution import client_id
from support import call, write

LISTED = ("DEMOA", "DEMOB", "DEMOC")
ACCOUNT = ["--account", "paper-test-account"]


@pytest.fixture(autouse=True)
def credentials(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "synthetic-test-key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "synthetic-test-secret")


class Venue:
    """A simulated paper venue that fills marketable orders at once and keeps every request it receives."""

    def __init__(self):
        self.requests = []
        self.cash = Decimal("1000")
        self.positions = {}
        self.orders = {}
        self.open = True
        self.untradable = set()
        self.refuse_submission = None  # (HTTP status, message) to answer every submission with
        self.after_submission = lambda: None

    def count(self, method, path):
        return sum(1 for r in self.requests if r.method == method and r.url.path == path)

    def place(self, order):
        qty, price = Decimal(order["qty"]), Decimal(order["limit_price"])
        self.positions[order["symbol"]] = self.positions.get(order["symbol"], 0) + qty
        self.cash -= qty * price
        self.orders[order["client_order_id"]] = {**order, "id": f"venue-{len(self.orders)}", "status": "filled",
                                                 "filled_qty": order["qty"], "filled_avg_price": order["limit_price"]}
        return self.orders[order["client_order_id"]]

    def asset(self, symbol):
        return {"symbol": symbol, "class": "us_equity", "tradable": symbol not in self.untradable}

    def __call__(self, request):
        self.requests.append(request)
        path = request.url.path
        if path == "/v2/account":
            return httpx.Response(200, json={"id": "paper-test-account", "status": "ACTIVE", "currency": "USD",
                                             "cash": str(self.cash), "equity": "1000"})
        if path == "/v2/positions":
            return httpx.Response(200, json=[{"symbol": s, "qty": str(q)} for s, q in self.positions.items()])
        if path == "/v2/clock":
            return httpx.Response(200, json={"is_open": self.open, "next_close": iso(now() + timedelta(hours=2))})
        if path == "/v2/orders" and request.method == "GET":
            return httpx.Response(200, json=[])
        if path == "/v2/orders" and request.method == "POST":
            if self.refuse_submission:
                status, message = self.refuse_submission
                return httpx.Response(status, json={"code": 40010001, "message": message})
            placed = self.place(json.loads(request.content))
            self.after_submission()
            return httpx.Response(200, json=placed)
        if path == "/v2/orders:by_client_order_id":
            order = self.orders.get(request.url.params["client_order_id"])
            return httpx.Response(200, json=order) if order else httpx.Response(404, json={"message": "not found"})
        if path == "/v2/assets":
            return httpx.Response(200, json=[self.asset(s) for s in LISTED])
        if path.startswith("/v2/assets/"):
            symbol = path.rsplit("/", 1)[1]
            if symbol in LISTED:
                return httpx.Response(200, json=self.asset(symbol))
            return httpx.Response(404, json={"message": "asset not found"})
        if path == "/v2/stocks/quotes/latest":
            return httpx.Response(200, json={"quotes": {s: {"bp": 99.9, "ap": 100, "t": iso(now())}
                                                        for s in request.url.params["symbols"].split(",")}})
        return httpx.Response(500, json={"message": "unexpected request"})


def client(venue):
    return AlpacaPaper(transport=httpx.MockTransport(venue))


def test_several_symbols_share_one_asset_listing():
    venue = Venue()
    broker = client(venue)
    try:
        result = broker.snapshot(["DEMOA", "DEMOB", "DEMOX"])
    finally:
        broker.close()
    assert result["assets"] == {"DEMOA": {"tradable": True}, "DEMOB": {"tradable": True},
                                "DEMOX": {"tradable": False}}
    assert [r.url.path for r in venue.requests] == ["/v2/account", "/v2/positions", "/v2/clock", "/v2/orders",
                                                    "/v2/stocks/quotes/latest", "/v2/assets"]
    assert dict(venue.requests[-1].url.params) == {"status": "active", "asset_class": "us_equity"}


def test_every_observation_reads_the_market_session_and_the_stock_afresh():
    venue = Venue()
    broker = client(venue)
    try:
        before = broker.snapshot(["DEMOA"])
        venue.open = False
        venue.untradable.add("DEMOA")
        after = broker.snapshot(["DEMOA"])
        unknown = broker.snapshot(["DEMOZ"])
    finally:
        broker.close()
    assert (before["market_open"], before["assets"]) == (True, {"DEMOA": {"tradable": True}})
    assert (after["market_open"], after["assets"]) == (False, {"DEMOA": {"tradable": False}})
    assert unknown["assets"] == {"DEMOZ": {"tradable": False}}
    assert venue.count("GET", "/v2/clock") == 3 and venue.count("GET", "/v2/assets/DEMOA") == 2
    assert venue.count("GET", "/v2/assets") == 0


def answering(status, message):
    return client(lambda request: httpx.Response(status, json={"code": 40010001, "message": message}
                                                 if message else {}))


@pytest.mark.parametrize("status, message", [
    (403, "insufficient buying power"), (422, "invalid order type"), (400, "invalid limit_price"),
    (429, "too many requests"), (401, ""),
])
def test_an_outright_rejection_shows_that_no_order_was_created(status, message):
    broker = answering(status, message)
    try:
        with pytest.raises(OrderRejected) as caught:
            broker.submit({"client_order_id": "synthetic"})
    finally:
        broker.close()
    assert (caught.value.status_code, caught.value.detail) == (status, message)
    assert str(caught.value) == ("Broker returned HTTP " + str(status) + (f": {message}" if message else "") +
                                 "; no automatic submission retry")


@pytest.mark.parametrize("status, message", [
    (422, "client_order_id must be unique"), (400, "Client Order ID is invalid"), (422, ""), (404, "not found"),
    (409, "conflict"),
])
def test_a_refusal_that_may_hide_an_order_leaves_the_submission_unresolved(status, message):
    broker = answering(status, message)
    try:
        with pytest.raises(BrokerRefused) as caught:
            broker.submit({"client_order_id": "synthetic"})
    finally:
        broker.close()
    assert not isinstance(caught.value, OrderRejected)


def test_a_refused_read_is_never_an_order_rejection():
    broker = answering(429, "too many requests")
    try:
        with pytest.raises(BrokerRefused) as caught:
            broker.account_id()
    finally:
        broker.close()
    assert not isinstance(caught.value, OrderRejected)


@pytest.mark.parametrize("status", [408, 500, 503])
def test_timeouts_and_server_errors_leave_a_submission_uncertain(status):
    broker = client(lambda request: httpx.Response(status, text="<html>busy</html>"))
    try:
        with pytest.raises(Refused, match=f"^Broker returned HTTP {status}; no automatic submission retry$") as caught:
            broker.submit({"client_order_id": "synthetic"})
    finally:
        broker.close()
    assert not isinstance(caught.value, BrokerRefused)


def paper_edition(tmp_path, author, payload, capsys, **changes):
    """A current paper edition installed from the command line; returns the global arguments for that state."""
    trust, sign = author
    started = now()
    payload.update(published_at=iso(started - timedelta(days=1)), information_cutoff=iso(started - timedelta(days=2)),
                   valid_until=iso(started + timedelta(days=30)), **changes)
    args = ["--state", tmp_path / "state", "--trust", write(tmp_path / "trust.json", trust)]
    assert call(capsys, args + ["install", write(tmp_path / "edition.json", sign(payload))])[0] == 0
    return args


def previewed(tmp_path, author, payload, monkeypatch, capsys, **changes):
    args = paper_edition(tmp_path, author, payload, capsys, **changes)
    venue = Venue()
    monkeypatch.setattr(cli, "AlpacaPaper", lambda: client(venue))
    code, preview = call(capsys, args + ["preview", "test-research"])
    assert code == 0
    return args, venue, preview


def test_a_paper_run_rereads_the_session_and_the_stock_before_each_order(tmp_path, author, payload, monkeypatch,
                                                                         capsys):
    args, venue, preview = previewed(tmp_path, author, payload, monkeypatch, capsys, universe=list(LISTED),
                                     targets={s: "0.3" for s in LISTED})
    orders = len(preview["plan"]["orders"])
    assert orders == 3
    assert len(venue.requests) == 6  # account, positions, clock, open orders, quotes, one asset listing
    venue.requests.clear()
    code, result = call(capsys, args + ["execute-paper", preview["plan_id"], *ACCOUNT])
    assert code == 0 and result["status"] == "complete"
    assert venue.count("GET", "/v2/clock") == orders and venue.count("GET", "/v2/assets") == 0
    assert [venue.count("GET", f"/v2/assets/{s}") for s in LISTED] == [1, 1, 1]
    # Once per command: the account binding. Per order: account, positions, clock, open orders, quotes and the
    # stock's tradability, the check that its client ID is unused, the submission and its lookup.
    assert len(venue.requests) == 1 + 9 * orders


@pytest.mark.parametrize("change, reason", [
    ("market closes", "Regular market session is closed"),
    ("next stock becomes untradable", "DEMOB: Asset is not tradable"),
])
def test_a_change_after_the_first_order_stops_the_next_one(tmp_path, author, payload, monkeypatch, capsys, change,
                                                           reason):
    args, venue, preview = previewed(tmp_path, author, payload, monkeypatch, capsys)
    assert [o["symbol"] for o in preview["plan"]["orders"]] == ["DEMOA", "DEMOB"]

    def after_submission():
        if change == "market closes":
            venue.open = False
        else:
            venue.untradable.add("DEMOB")

    venue.after_submission = after_submission
    code, refusal = call(capsys, args + ["execute-paper", preview["plan_id"], *ACCOUNT])
    assert code == 2 and refusal["reason"] == reason
    assert venue.count("POST", "/v2/orders") == 1


def test_an_outright_rejection_halts_the_plan_and_a_fresh_preview_is_allowed(tmp_path, author, payload, monkeypatch,
                                                                             capsys):
    args, venue, preview = previewed(tmp_path, author, payload, monkeypatch, capsys)
    venue.refuse_submission = (403, "insufficient buying power")
    code, result = call(capsys, args + ["execute-paper", preview["plan_id"], *ACCOUNT])
    assert code == 0 and result == {
        "plan_id": preview["plan_id"], "status": "halted", "order_status": "submission_rejected", "symbol": "DEMOA",
        "reason": "Broker returned HTTP 403: insufficient buying power; no automatic submission retry",
        "next_step": "Inspect fills and create a fresh preview"}
    halted = {"plan_id": preview["plan_id"], "status": "halted"}
    assert call(capsys, args + ["execute-paper", preview["plan_id"], *ACCOUNT]) == (0, halted)
    assert call(capsys, args + ["cancel-paper", preview["plan_id"], *ACCOUNT]) == (0, halted)
    venue.refuse_submission = None
    code, fresh = call(capsys, args + ["preview", "test-research"])
    assert code == 0 and fresh["plan_id"] != preview["plan_id"]
    assert venue.count("POST", "/v2/orders") == 1


def test_a_client_id_in_use_keeps_the_plan_unresolved_until_the_broker_shows_the_order(tmp_path, author, payload,
                                                                                       monkeypatch, capsys):
    args, venue, preview = previewed(tmp_path, author, payload, monkeypatch, capsys)
    plan_id = preview["plan_id"]
    venue.refuse_submission = (422, "client_order_id must be unique")
    code, refusal = call(capsys, args + ["execute-paper", plan_id, *ACCOUNT])
    assert code == 2 and refusal["reason"] == ("Broker returned HTTP 422: client_order_id must be unique; "
                                               "no automatic submission retry")
    assert call(capsys, args + ["preview", "test-research"]) == (2, {
        "status": "refused", "reason": f"Reconcile or cancel the outstanding execution first: plan {plan_id}"})
    assert call(capsys, args + ["cancel-paper", plan_id, *ACCOUNT]) == (2, {
        "status": "refused",
        "reason": "DEMOA: Submission outcome is uncertain; no retry. Inspect broker history manually"})
    # The order that holds the ID becomes visible: the plan reconciles with it and nothing is sent twice.
    venue.refuse_submission = None
    venue.place({**preview["plan"]["orders"][0], "client_order_id": client_id(plan_id, 0)})
    code, result = call(capsys, args + ["execute-paper", plan_id, *ACCOUNT])
    assert code == 0 and result["status"] == "complete"
    assert venue.positions == {"DEMOA": 3, "DEMOB": 3} and venue.count("POST", "/v2/orders") == 2
