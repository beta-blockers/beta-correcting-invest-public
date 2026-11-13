"""How many requests the paper broker client makes, what it reads before each order, how it classifies refused
submissions, and how it finds an order. A simulated venue answers every request; all symbols and values are
fictional."""
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
LONG_PREFIX = "the order could not be accepted because " * 6  # 240 characters, past the shortened reason
ESCAPED_DUPLICATE = '{"code":40310000,"message":"client\\u005forder\\u005fid must be unique"}'


@pytest.fixture(autouse=True)
def credentials(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "synthetic-test-key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "synthetic-test-secret")


def alpaca_error(message, code=40310000, **fields):
    return json.dumps({"code": code, "message": message, **fields})


class Venue:
    """A simulated paper venue that keeps every request it receives. It fills marketable orders at once unless told
    not to, and can be made to miss orders when they are looked up by client order ID."""

    def __init__(self):
        self.requests = []
        self.cash = Decimal("1000")
        self.positions = {}
        self.orders = {}
        self.open = True
        self.untradable = set()
        self.fill = True
        self.blind = False  # lookups by client order ID answer 404
        self.refuse_submission = None  # (HTTP status, response text) to answer every submission with
        self.after_submission = lambda: None

    def count(self, method, path):
        return sum(1 for r in self.requests if r.method == method and r.url.path == path)

    def place(self, order):
        placed = {**order, "id": f"venue-{len(self.orders)}", "status": "accepted", "filled_qty": "0",
                  "filled_avg_price": None}
        if self.fill:
            qty, price = Decimal(order["qty"]), Decimal(order["limit_price"])
            self.positions[order["symbol"]] = self.positions.get(order["symbol"], 0) + qty
            self.cash -= qty * price
            placed.update(status="filled", filled_qty=order["qty"], filled_avg_price=order["limit_price"])
        self.orders[order["client_order_id"]] = placed
        return placed

    def by_id(self, broker_id):
        return next((o for o in self.orders.values() if o["id"] == broker_id), None)

    def asset(self, symbol):
        return {"symbol": symbol, "class": "us_equity", "tradable": symbol not in self.untradable}

    def __call__(self, request):
        self.requests.append(request)
        path, method = request.url.path, request.method
        if path == "/v2/account":
            return httpx.Response(200, json={"id": "paper-test-account", "status": "ACTIVE", "currency": "USD",
                                             "cash": str(self.cash), "equity": "1000"})
        if path == "/v2/positions":
            return httpx.Response(200, json=[{"symbol": s, "qty": str(q)} for s, q in self.positions.items()])
        if path == "/v2/clock":
            return httpx.Response(200, json={"is_open": self.open, "next_close": iso(now() + timedelta(hours=2))})
        if path == "/v2/orders" and method == "GET":
            return httpx.Response(200, json=[])
        if path == "/v2/orders" and method == "POST":
            if self.refuse_submission:
                status, text = self.refuse_submission
                return httpx.Response(status, text=text, headers={"content-type": "application/json"})
            placed = self.place(json.loads(request.content))
            self.after_submission()
            return httpx.Response(200, json=placed)
        if path == "/v2/orders:by_client_order_id":
            order = self.orders.get(request.url.params["client_order_id"])
            if order and not self.blind:
                return httpx.Response(200, json=order)
            return httpx.Response(404, json={"message": "order not found"})
        if path.startswith("/v2/orders/"):
            order = self.by_id(path.rsplit("/", 1)[1])
            if order is None:
                return httpx.Response(404, json={"message": "order not found"})
            if method == "DELETE":
                order["status"] = "canceled"
                return httpx.Response(204)
            return httpx.Response(200, json=order)
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


def submission_answered(status, text):
    """What submitting an order raises when the broker answers with this status and response text."""
    broker = client(lambda request: httpx.Response(status, text=text, headers={"content-type": "application/json"}))
    try:
        with pytest.raises(Refused) as caught:
            broker.submit({"client_order_id": "synthetic"})
    finally:
        broker.close()
    return caught.value


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


@pytest.mark.parametrize("status, text", [
    (403, alpaca_error("insufficient buying power", buying_power="558660.03", cost_basis="680930026.5")),
    (403, alpaca_error("insufficient qty available for order (requested: 5, available: 3)")),
    (403, alpaca_error("account is not authorized to trade")),
    (403, alpaca_error("account is restricted to liquidation only")),
    (403, alpaca_error("Account  is not allowed to short")),
    (429, alpaca_error("too many requests", code=42910000)),
    (429, "Too Many Requests"),
    (401, '{"message": "unauthorized"}'),
])
def test_a_recognized_rejection_shows_that_no_order_was_created(status, text):
    refusal = submission_answered(status, text)
    assert isinstance(refusal, OrderRejected) and refusal.status_code == status


@pytest.mark.parametrize("status, text", [
    (422, alpaca_error("client_order_id must be unique", code=40010001)),
    (422, alpaca_error("invalid order type", code=40010001)),
    (400, alpaca_error("invalid limit_price", code=40010001)),
    (422, "{}"),
    (404, alpaca_error("not found")),
    (409, alpaca_error("conflict")),
    (403, alpaca_error("forbidden")),
    (403, alpaca_error("")),
    (403, "Forbidden"),
    (403, alpaca_error("insufficient buying power; client order ID already in use")),
    (403, alpaca_error("Client Order ID already in use")),
    (429, alpaca_error("duplicate submission", code=42910000)),
])
def test_any_other_refusal_leaves_the_submission_unresolved(status, text):
    refusal = submission_answered(status, text)
    assert isinstance(refusal, BrokerRefused) and not isinstance(refusal, OrderRejected)


@pytest.mark.parametrize("status, text", [
    (403, ESCAPED_DUPLICATE),
    (403, '{"code":40310000,"message":"insufficient buying power","client\\u005forder\\u005fid":"in use"}'),
    (429, '{"code":42910000,"message":"\\u0064uplicate submission"}'),
])
def test_escaped_text_is_decoded_before_it_is_classified(status, text):
    refusal = submission_answered(status, text)
    assert isinstance(refusal, BrokerRefused) and not isinstance(refusal, OrderRejected)
    assert refusal.detail == json.loads(text)["message"]


@pytest.mark.parametrize("status, body", [
    (422, {"code": 40010001, "message": LONG_PREFIX + "client_order_id must be unique"}),
    (403, {"code": 40310000, "message": LONG_PREFIX + "client_order_id must be unique"}),
    (403, {"code": 40310000, "message": "forbidden", "field": "client_order_id"}),
])
def test_the_whole_response_is_classified_and_only_the_displayed_reason_is_shortened(status, body):
    refusal = submission_answered(status, json.dumps(body))
    assert isinstance(refusal, BrokerRefused) and not isinstance(refusal, OrderRejected)
    assert refusal.detail == " ".join(body["message"].split())[:200]
    assert len(body["message"]) < 200 or "client_order_id" not in refusal.detail


def test_a_refused_read_is_never_an_order_rejection():
    broker = client(lambda request: httpx.Response(429, text=alpaca_error("too many requests", code=42910000)))
    try:
        with pytest.raises(BrokerRefused) as caught:
            broker.account_id()
    finally:
        broker.close()
    assert not isinstance(caught.value, OrderRejected)


@pytest.mark.parametrize("status", [408, 500, 503])
def test_timeouts_and_server_errors_leave_a_submission_uncertain(status):
    refusal = submission_answered(status, "<html>busy</html>")
    assert not isinstance(refusal, BrokerRefused)
    assert str(refusal) == f"Broker returned HTTP {status}; no automatic submission retry"


def test_an_order_is_looked_up_by_the_brokers_own_id():
    venue = Venue()
    placed = venue.place({"client_order_id": "synthetic", "symbol": "DEMOA", "side": "buy", "qty": "1",
                          "type": "limit", "time_in_force": "day", "limit_price": "100.25", "extended_hours": False})
    broker = client(venue)
    try:
        assert broker.order(placed["id"]) == placed
        assert broker.order("venue-unknown") is None
    finally:
        broker.close()
    assert [r.url.path for r in venue.requests] == [f"/v2/orders/{placed['id']}", "/v2/orders/venue-unknown"]


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


def test_a_recognized_rejection_halts_the_plan_and_a_fresh_preview_is_allowed(tmp_path, author, payload, monkeypatch,
                                                                             capsys):
    args, venue, preview = previewed(tmp_path, author, payload, monkeypatch, capsys)
    venue.refuse_submission = (403, alpaca_error("insufficient buying power"))
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


@pytest.mark.parametrize("status, text", [
    (422, alpaca_error("client_order_id must be unique", code=40010001)),
    (422, alpaca_error(LONG_PREFIX + "client_order_id must be unique", code=40010001)),
    (403, alpaca_error(LONG_PREFIX + "client_order_id must be unique")),
    (403, ESCAPED_DUPLICATE),
])
def test_a_client_id_in_use_keeps_the_plan_unresolved_until_the_broker_shows_the_order(tmp_path, author, payload,
                                                                                       monkeypatch, capsys, status,
                                                                                       text):
    args, venue, preview = previewed(tmp_path, author, payload, monkeypatch, capsys)
    plan_id = preview["plan_id"]
    venue.refuse_submission = (status, text)
    code, refusal = call(capsys, args + ["execute-paper", plan_id, *ACCOUNT])
    shown = " ".join(json.loads(text)["message"].split())[:200]
    assert code == 2 and refusal["reason"] == f"Broker returned HTTP {status}: {shown}; no automatic submission retry"
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


@pytest.mark.parametrize("canceled_by", ["broker", "cancel-paper"])
def test_the_saved_alpaca_order_id_settles_an_order_that_a_client_id_lookup_misses(tmp_path, author, payload,
                                                                                   monkeypatch, capsys, canceled_by):
    args, venue, preview = previewed(tmp_path, author, payload, monkeypatch, capsys)
    plan_id, coid = preview["plan_id"], client_id(preview["plan_id"], 0)
    venue.fill, venue.blind = False, True
    code, result = call(capsys, args + ["execute-paper", plan_id, *ACCOUNT])
    assert code == 0 and result["status"] == "pending" and result["symbol"] == "DEMOA"
    by_id = f"/v2/orders/{venue.orders[coid]['id']}"
    if canceled_by == "broker":
        venue.orders[coid]["status"] = "canceled"
        assert call(capsys, args + ["execute-paper", plan_id, *ACCOUNT]) == (0, {
            "plan_id": plan_id, "status": "halted", "order_status": "canceled", "symbol": "DEMOA",
            "next_step": "Inspect fills and create a fresh preview"})
        assert call(capsys, args + ["cancel-paper", plan_id, *ACCOUNT]) == (0, {"plan_id": plan_id, "status": "halted"})
    else:
        assert call(capsys, args + ["cancel-paper", plan_id, *ACCOUNT]) == (0, {"plan_id": plan_id,
                                                                               "status": "canceled"})
        assert venue.count("DELETE", by_id) == 1 and venue.orders[coid]["status"] == "canceled"
    assert venue.count("GET", by_id) >= 2 and venue.count("POST", "/v2/orders") == 1
    assert call(capsys, args + ["preview", "test-research"])[0] == 0
