"""How many requests the paper broker client makes, and how it reports refusals. A simulated venue answers every
request; all symbols and values are fictional."""
from datetime import timedelta
from decimal import Decimal
import json

import httpx
import pytest

from conftest import AT
from public_pilot import cli
from public_pilot.broker import AlpacaPaper, BrokerRefused
from public_pilot.common import Refused, iso, now
from support import call, write

LISTED = ("DEMOA", "DEMOB", "DEMOC")


@pytest.fixture(autouse=True)
def credentials(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "synthetic-test-key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "synthetic-test-secret")


class Venue:
    """A simulated paper venue that fills marketable orders at once and keeps every request it receives."""

    def __init__(self, clock=now, close=None):
        self.clock = clock
        self.close = close
        self.requests = []
        self.cash = Decimal("1000")
        self.positions = {}
        self.orders = {}
        self.refuse_submission = None  # (HTTP status, message) for an outright refusal of submissions

    def count(self, method, path):
        return sum(1 for r in self.requests if r.method == method and r.url.path == path)

    def __call__(self, request):
        self.requests.append(request)
        path, at = request.url.path, self.clock()
        if path == "/v2/account":
            return httpx.Response(200, json={"id": "paper-test-account", "status": "ACTIVE", "currency": "USD",
                                             "cash": str(self.cash), "equity": "1000"})
        if path == "/v2/positions":
            return httpx.Response(200, json=[{"symbol": s, "qty": str(q)} for s, q in self.positions.items()])
        if path == "/v2/clock":
            close = self.close or at + timedelta(hours=2)
            return httpx.Response(200, json={"is_open": at < close, "next_close": iso(close)})
        if path == "/v2/orders" and request.method == "GET":
            return httpx.Response(200, json=[])
        if path == "/v2/orders" and request.method == "POST":
            if self.refuse_submission:
                status, message = self.refuse_submission
                return httpx.Response(status, json={"code": 40310000, "message": message})
            order = json.loads(request.content)
            qty, price = Decimal(order["qty"]), Decimal(order["limit_price"])
            self.positions[order["symbol"]] = self.positions.get(order["symbol"], 0) + qty
            self.cash -= qty * price
            created = {**order, "id": f"venue-{len(self.orders)}", "status": "filled",
                       "filled_qty": order["qty"], "filled_avg_price": order["limit_price"]}
            self.orders[order["client_order_id"]] = created
            return httpx.Response(200, json=created)
        if path == "/v2/orders:by_client_order_id":
            order = self.orders.get(request.url.params["client_order_id"])
            return httpx.Response(200, json=order) if order else httpx.Response(404, json={"message": "not found"})
        if path == "/v2/assets":
            return httpx.Response(200, json=[{"symbol": s, "class": "us_equity", "tradable": True} for s in LISTED])
        if path.startswith("/v2/assets/"):
            symbol = path.rsplit("/", 1)[1]
            if symbol in LISTED:
                return httpx.Response(200, json={"symbol": symbol, "class": "us_equity", "tradable": True})
            return httpx.Response(404, json={"message": "asset not found"})
        if path == "/v2/stocks/quotes/latest":
            return httpx.Response(200, json={"quotes": {s: {"bp": 99.9, "ap": 100, "t": iso(at)}
                                                        for s in request.url.params["symbols"].split(",")}})
        return httpx.Response(500, json={"message": "unexpected request"})


def client(venue):
    return AlpacaPaper(transport=httpx.MockTransport(venue))


def test_several_symbols_cost_one_asset_listing_and_the_clock_is_read_once(monkeypatch):
    monkeypatch.setattr("public_pilot.broker.now", lambda: AT)
    venue = Venue(clock=lambda: AT)
    broker = client(venue)
    try:
        first = broker.snapshot(["DEMOA", "DEMOB", "DEMOX"])
        second = broker.snapshot(["DEMOA", "DEMOB", "DEMOX"])
    finally:
        broker.close()
    tradability = {"DEMOA": {"tradable": True}, "DEMOB": {"tradable": True}, "DEMOX": {"tradable": False}}
    assert first["assets"] == second["assets"] == tradability
    assert first["market_open"] is True and second["market_open"] is True
    listing = [r for r in venue.requests if r.url.path == "/v2/assets"]
    assert len(listing) == 1
    assert dict(listing[0].url.params) == {"status": "active", "asset_class": "us_equity"}
    assert not [r for r in venue.requests if r.url.path.startswith("/v2/assets/")]
    assert venue.count("GET", "/v2/clock") == 1
    # The second observation reads only the account, positions, open orders and quotes.
    assert len(venue.requests) == 6 + 4


def test_a_single_unknown_symbol_is_looked_up_directly_and_an_unknown_one_is_not_tradable(monkeypatch):
    monkeypatch.setattr("public_pilot.broker.now", lambda: AT)
    venue = Venue(clock=lambda: AT)
    broker = client(venue)
    try:
        assert broker.snapshot(["DEMOZ"])["assets"] == {"DEMOZ": {"tradable": False}}
        assert broker.snapshot(["DEMOA"])["assets"] == {"DEMOA": {"tradable": True}}
    finally:
        broker.close()
    assert venue.count("GET", "/v2/assets/DEMOZ") == 1 and venue.count("GET", "/v2/assets/DEMOA") == 1
    assert venue.count("GET", "/v2/assets") == 0


def test_the_clock_is_read_again_from_a_minute_before_the_close(monkeypatch):
    instant = [AT]
    monkeypatch.setattr("public_pilot.broker.now", lambda: instant[0])
    venue = Venue(clock=lambda: instant[0], close=AT + timedelta(minutes=30))
    broker = client(venue)
    try:
        for minutes, is_open, readings in [(0, True, 1), (28, True, 1), (29.5, True, 2), (29.75, True, 3),
                                           (30, False, 4), (31, False, 5)]:
            instant[0] = AT + timedelta(minutes=minutes)
            assert broker.snapshot(["DEMOA"])["market_open"] is is_open
            assert venue.count("GET", "/v2/clock") == readings
    finally:
        broker.close()


@pytest.mark.parametrize("status", [400, 403, 422, 429])
def test_client_errors_are_refusals_that_carry_the_brokers_reason(status):
    broker = client(lambda request: httpx.Response(status, json={"code": 40310000,
                                                                 "message": "insufficient\n buying power"}))
    try:
        with pytest.raises(BrokerRefused) as caught:
            broker.submit({"client_order_id": "synthetic"})
    finally:
        broker.close()
    assert caught.value.status_code == status and caught.value.detail == "insufficient buying power"
    assert str(caught.value) == (f"Broker returned HTTP {status}: insufficient buying power; "
                                 "no automatic submission retry")


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


def test_a_paper_run_reads_the_clock_and_the_asset_listing_once_per_command(tmp_path, author, payload, monkeypatch,
                                                                           capsys):
    args = paper_edition(tmp_path, author, payload, capsys, universe=list(LISTED),
                         targets={s: "0.3" for s in LISTED})
    venue = Venue()
    monkeypatch.setattr(cli, "AlpacaPaper", lambda: client(venue))
    code, preview = call(capsys, args + ["preview", "test-research"])
    assert code == 0 and len(preview["plan"]["orders"]) == 3
    assert len(venue.requests) == 6  # account, positions, clock, open orders, quotes, one asset listing
    venue.requests.clear()
    execute = ["execute-paper", preview["plan_id"], "--account", "paper-test-account"]
    code, result = call(capsys, args + execute)
    assert code == 0 and result["status"] == "complete"
    orders = len(preview["plan"]["orders"])
    assert venue.count("GET", "/v2/clock") == 1 and venue.count("GET", "/v2/assets") == 1
    assert venue.count("GET", "/v2/account") == 1 + orders
    # Once per command: account binding, clock, asset listing. Per order: account, positions, open orders,
    # quotes, the check that its client ID is unused, the submission and its lookup.
    assert len(venue.requests) == 3 + 7 * orders


def test_an_outright_refusal_halts_the_plan_and_a_fresh_preview_is_allowed(tmp_path, author, payload, monkeypatch,
                                                                           capsys):
    args = paper_edition(tmp_path, author, payload, capsys)
    venue = Venue()
    monkeypatch.setattr(cli, "AlpacaPaper", lambda: client(venue))
    code, preview = call(capsys, args + ["preview", "test-research"])
    assert code == 0
    venue.refuse_submission = (403, "insufficient buying power")
    account = ["--account", "paper-test-account"]
    code, result = call(capsys, args + ["execute-paper", preview["plan_id"], *account])
    assert code == 0 and result == {
        "plan_id": preview["plan_id"], "status": "halted", "order_status": "submission_refused", "symbol": "DEMOA",
        "reason": "Broker returned HTTP 403: insufficient buying power; no automatic submission retry",
        "next_step": "Inspect fills and create a fresh preview"}
    halted = {"plan_id": preview["plan_id"], "status": "halted"}
    assert call(capsys, args + ["execute-paper", preview["plan_id"], *account]) == (0, halted)
    assert call(capsys, args + ["cancel-paper", preview["plan_id"], *account]) == (0, halted)
    venue.refuse_submission = None
    code, fresh = call(capsys, args + ["preview", "test-research"])
    assert code == 0 and fresh["plan_id"] != preview["plan_id"]
    assert venue.count("POST", "/v2/orders") == 1
