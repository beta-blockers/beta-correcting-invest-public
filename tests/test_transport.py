import httpx
import pytest

from public_pilot.broker import AlpacaPaper, PAPER
from public_pilot.common import Refused


def test_redirects_are_not_followed_and_environment_cannot_change_endpoint(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "synthetic-test-key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "synthetic-test-secret")
    monkeypatch.setenv("APCA_API_BASE_URL", "https://untrusted.invalid")
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(302, headers={"Location": "https://untrusted.invalid"})

    broker = AlpacaPaper(transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(Refused, match="302"):
            broker.account_id()
        assert len(requests) == 1
        assert str(requests[0].url) == PAPER + "/v2/account"
    finally:
        broker.close()


def test_transport_failure_does_not_retry_post(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "synthetic-test-key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "synthetic-test-secret")
    requests = []

    def handle(request):
        requests.append(request)
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    broker = AlpacaPaper(transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(Refused, match="reconciliation"):
            broker.submit({"client_order_id": "synthetic"})
        assert len(requests) == 1
    finally:
        broker.close()


def test_snapshot_adapts_account_assets_and_iex_quotes(monkeypatch):
    from conftest import AT
    from public_pilot.common import iso

    monkeypatch.setenv("APCA_API_KEY_ID", "synthetic-test-key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "synthetic-test-secret")
    monkeypatch.setattr("public_pilot.broker.now", lambda: AT)
    requested = []

    def handle(request):
        requested.append(request)
        path = request.url.path
        bodies = {
            "/v2/account": {"id": "test-account", "status": "ACTIVE", "currency": "USD", "cash": "1000", "equity": "1000"},
            "/v2/positions": [], "/v2/clock": {"is_open": True}, "/v2/orders": [],
            "/v2/assets/DEMOA": {"class": "us_equity", "tradable": True},
            "/v2/stocks/quotes/latest": {"quotes": {"DEMOA": {"bp": 99.9, "ap": 100, "t": iso(AT)}}},
        }
        return httpx.Response(200, json=bodies[path])

    broker = AlpacaPaper(transport=httpx.MockTransport(handle))
    try:
        result = broker.snapshot(["DEMOA"])
        assert result["account_id"] == "test-account"
        assert result["quotes"]["DEMOA"]["ask"] == "100"
        assert result["assets"]["DEMOA"]["tradable"] is True
        data_request = next(r for r in requested if r.url.host == "data.alpaca.markets")
        assert data_request.url.params["feed"] == "iex"
        assert all(r.method == "GET" for r in requested)
    finally:
        broker.close()
