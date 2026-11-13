"""Alpaca PAPER endpoint only. Credentials are never supplied by a research package."""
from __future__ import annotations

from datetime import timedelta
import os
from urllib.parse import quote as urlquote

import httpx

from .common import Refused, iso, now, require, timestamp

PAPER = "https://paper-api.alpaca.markets"
DATA = "https://data.alpaca.markets"
# An open clock reading is reused until this long before the close it reports; after that, every observation
# asks the broker again, exactly as if nothing were reused.
CLOCK_REUSE_MARGIN = timedelta(minutes=1)


class BrokerRefused(Refused):
    """The broker answered with a client error (HTTP 4xx other than 408 Request Timeout): it received the request
    and did not carry it out. For an order submission, this means no order was created."""

    def __init__(self, message, status_code, detail):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


def _detail(response):
    """The broker's own explanation of an error response, shortened; empty when it gave none."""
    try:
        body = response.json()
    except ValueError:
        return ""
    message = body.get("message") if isinstance(body, dict) else None
    return " ".join(str(message).split())[:200] if message else ""


def tradable_equity(asset):
    return isinstance(asset, dict) and asset.get("tradable") is True and asset.get("class") == "us_equity"


class AlpacaPaper:
    def __init__(self, *, transport=None):
        key = os.environ.get("APCA_API_KEY_ID")
        secret = os.environ.get("APCA_API_SECRET_KEY")
        require(key and secret, "Set APCA_API_KEY_ID and APCA_API_SECRET_KEY for your paper account")
        self.client = httpx.Client(headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret},
                                   timeout=15, trust_env=False, follow_redirects=False, transport=transport)
        # One client serves one command. Asset tradability and an open clock reading are reused within it.
        self._tradable = {}
        self._open_until = None

    def close(self):
        self.client.close()

    def _request(self, method, path, *, data=False, absent_ok=False, **kwargs):
        require(path.startswith("/v2/") and ".." not in path, "Invalid broker path")
        try:
            response = self.client.request(method, (DATA if data else PAPER) + path, **kwargs)
        except httpx.RequestError as exc:
            raise Refused("Broker transport failed; any attempted submission requires reconciliation") from exc
        if response.status_code == 404 and absent_ok:
            return None
        if not 200 <= response.status_code < 300:
            detail = _detail(response)
            message = (f"Broker returned HTTP {response.status_code}" + (f": {detail}" if detail else "") +
                       "; no automatic submission retry")
            if 400 <= response.status_code < 500 and response.status_code != 408:
                raise BrokerRefused(message, response.status_code, detail)
            raise Refused(message)
        return response.json() if response.content else None

    def _market_open(self):
        """Whether the regular session is open. An open reading answers again until shortly before its close."""
        if self._open_until is not None and now() < self._open_until:
            return True
        clock = self._request("GET", "/v2/clock")
        is_open = clock.get("is_open") is True
        self._open_until = None
        if is_open and isinstance(clock.get("next_close"), str):
            self._open_until = timestamp(clock["next_close"]) - CLOCK_REUSE_MARGIN
        return is_open

    def _tradability(self, symbols):
        """Whether each symbol is a tradable US equity, asked at most once per symbol: a single unknown symbol is
        looked up directly, and one listing of active US equities answers several at once."""
        unknown = [s for s in symbols if s not in self._tradable]
        if len(unknown) == 1:
            asset = self._request("GET", "/v2/assets/" + urlquote(unknown[0], safe=""), absent_ok=True)
            self._tradable[unknown[0]] = tradable_equity(asset)
        elif unknown:
            listing = self._request("GET", "/v2/assets", params={"status": "active", "asset_class": "us_equity"})
            require(isinstance(listing, list), "Unexpected asset listing")
            assets = {a.get("symbol"): a for a in listing if isinstance(a, dict)}
            self._tradable.update({s: tradable_equity(assets.get(s)) for s in unknown})
        return {s: self._tradable[s] for s in symbols}

    def snapshot(self, universe):
        observed_at = iso(now())
        account = self._request("GET", "/v2/account")
        require(account.get("status") == "ACTIVE" and not account.get("trading_blocked")
                and not account.get("account_blocked"), "Paper account is not enabled for trading")
        require(account.get("currency") == "USD", "Only USD paper accounts are supported")
        held = self._request("GET", "/v2/positions")
        market_open = self._market_open()
        opened = self._request("GET", "/v2/orders", params={"status": "open", "limit": 500})
        require(len(opened) < 500, "Open-order listing may be truncated")
        symbols = sorted(set(universe) | {p["symbol"] for p in held})
        quotes = self._request("GET", "/v2/stocks/quotes/latest", data=True,
                               params={"symbols": ",".join(symbols), "feed": "iex"})["quotes"]
        tradable = self._tradability(symbols)
        return {"account_id": account["id"], "cash": account["cash"], "equity": account["equity"],
                "positions": {p["symbol"]: p["qty"] for p in held}, "observed_at": observed_at,
                "market_open": market_open, "open_orders": opened,
                "quotes": {s: {"bid": str(q["bp"]), "ask": str(q["ap"]), "at": q["t"]}
                           for s, q in quotes.items() if q is not None},
                "assets": {s: {"tradable": tradable[s]} for s in symbols}}

    def account_id(self):
        return self._request("GET", "/v2/account")["id"]

    def lookup(self, client_order_id):
        return self._request("GET", "/v2/orders:by_client_order_id", absent_ok=True,
                             params={"client_order_id": client_order_id})

    def submit(self, order):
        return self._request("POST", "/v2/orders", json=order)

    def cancel(self, broker_order_id):
        return self._request("DELETE", "/v2/orders/" + urlquote(broker_order_id, safe=""))
