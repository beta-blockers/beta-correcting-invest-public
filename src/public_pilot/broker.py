"""Alpaca PAPER endpoint only. Credentials are never supplied by a research package."""
from __future__ import annotations

import os
import re
from urllib.parse import quote as urlquote

import httpx

from .common import Refused, iso, now, require

PAPER = "https://paper-api.alpaca.markets"
DATA = "https://data.alpaca.markets"
# Answers to an order submission after which no order exists under its client order ID: invalid credentials, a
# broker rule such as insufficient buying power, and rate limiting. A 400 or 422 never counts: Alpaca answers 422
# both for a malformed order, which this engine does not send, and, with "client_order_id must be unique", when
# another active order already holds the ID. Nor does an answer that mentions the client order ID or a duplicate.
REJECTED = {401, 403, 429}


class BrokerRefused(Refused):
    """The broker answered with a client error (HTTP 4xx other than 408 Request Timeout) and did not carry out the
    request. For an order submission, this alone does not prove that no order exists under its client ID."""

    def __init__(self, message, status_code, detail, body=""):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail  # the broker's reason, shortened for display
        self.body = body  # the complete response, which alone is used to classify it


class OrderRejected(BrokerRefused):
    """The broker rejected an order submission outright: it created no order."""


def _detail(response):
    """The broker's own explanation of an error response, shortened for display; empty when it gave none."""
    try:
        body = response.json()
    except ValueError:
        return ""
    message = body.get("message") if isinstance(body, dict) else None
    return " ".join(str(message).split())[:200] if message else ""


def rejects_order(status_code, body):
    """Whether this answer to a submission shows that the broker created no order. The complete response is read,
    letters only, so that no spelling or length of a mention of the client order ID or a duplicate escapes."""
    letters = re.sub(r"[^a-z]", "", body.lower())
    return status_code in REJECTED and "clientorderid" not in letters and "duplicate" not in letters


def tradable_equity(asset):
    return isinstance(asset, dict) and asset.get("tradable") is True and asset.get("class") == "us_equity"


class AlpacaPaper:
    def __init__(self, *, transport=None):
        key = os.environ.get("APCA_API_KEY_ID")
        secret = os.environ.get("APCA_API_SECRET_KEY")
        require(key and secret, "Set APCA_API_KEY_ID and APCA_API_SECRET_KEY for your paper account")
        self.client = httpx.Client(headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret},
                                   timeout=15, trust_env=False, follow_redirects=False, transport=transport)

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
                raise BrokerRefused(message, response.status_code, detail, response.text)
            raise Refused(message)
        return response.json() if response.content else None

    def _tradability(self, symbols):
        """Whether each symbol is a tradable US equity, read afresh: a single symbol is looked up directly, and one
        listing of active US equities answers several at once."""
        if len(symbols) == 1:
            asset = self._request("GET", "/v2/assets/" + urlquote(symbols[0], safe=""), absent_ok=True)
            return {symbols[0]: tradable_equity(asset)}
        if not symbols:
            return {}
        listing = self._request("GET", "/v2/assets", params={"status": "active", "asset_class": "us_equity"})
        require(isinstance(listing, list), "Unexpected asset listing")
        assets = {a.get("symbol"): a for a in listing if isinstance(a, dict)}
        return {s: tradable_equity(assets.get(s)) for s in symbols}

    def snapshot(self, symbols):
        """The account, its positions and open orders, the market session, and quotes and tradability for these
        symbols. A preview passes its whole universe; execution passes only the symbol of the next order."""
        observed_at = iso(now())
        account = self._request("GET", "/v2/account")
        require(account.get("status") == "ACTIVE" and not account.get("trading_blocked")
                and not account.get("account_blocked"), "Paper account is not enabled for trading")
        require(account.get("currency") == "USD", "Only USD paper accounts are supported")
        held = self._request("GET", "/v2/positions")
        clock = self._request("GET", "/v2/clock")
        opened = self._request("GET", "/v2/orders", params={"status": "open", "limit": 500})
        require(len(opened) < 500, "Open-order listing may be truncated")
        quoted = sorted(set(symbols) | {p["symbol"] for p in held})
        quotes = self._request("GET", "/v2/stocks/quotes/latest", data=True,
                               params={"symbols": ",".join(quoted), "feed": "iex"})["quotes"]
        tradable = self._tradability(sorted(set(symbols)))
        return {"account_id": account["id"], "cash": account["cash"], "equity": account["equity"],
                "positions": {p["symbol"]: p["qty"] for p in held}, "observed_at": observed_at,
                "market_open": clock.get("is_open") is True, "open_orders": opened,
                "quotes": {s: {"bid": str(q["bp"]), "ask": str(q["ap"]), "at": q["t"]}
                           for s, q in quotes.items() if q is not None},
                "assets": {s: {"tradable": t} for s, t in tradable.items()}}

    def account_id(self):
        return self._request("GET", "/v2/account")["id"]

    def lookup(self, client_order_id):
        return self._request("GET", "/v2/orders:by_client_order_id", absent_ok=True,
                             params={"client_order_id": client_order_id})

    def submit(self, order):
        try:
            return self._request("POST", "/v2/orders", json=order)
        except BrokerRefused as exc:
            if rejects_order(exc.status_code, exc.body):
                raise OrderRejected(str(exc), exc.status_code, exc.detail, exc.body) from exc
            raise

    def cancel(self, broker_order_id):
        return self._request("DELETE", "/v2/orders/" + urlquote(broker_order_id, safe=""))
