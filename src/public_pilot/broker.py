"""Alpaca PAPER endpoint only. Credentials are never supplied by a research package."""
from __future__ import annotations

import os
from urllib.parse import quote as urlquote

import httpx

from .common import Refused, iso, now, require

PAPER = "https://paper-api.alpaca.markets"
DATA = "https://data.alpaca.markets"


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
        require(200 <= response.status_code < 300,
                f"Broker returned HTTP {response.status_code}; no automatic submission retry")
        return response.json() if response.content else None

    def snapshot(self, universe):
        observed_at = iso(now())
        account = self._request("GET", "/v2/account")
        require(account.get("status") == "ACTIVE" and not account.get("trading_blocked")
                and not account.get("account_blocked"), "Paper account is not enabled for trading")
        require(account.get("currency") == "USD", "Only USD paper accounts are supported")
        held = self._request("GET", "/v2/positions")
        clock = self._request("GET", "/v2/clock")
        opened = self._request("GET", "/v2/orders", params={"status": "open", "limit": 500})
        require(len(opened) < 500, "Open-order listing may be truncated")
        symbols = sorted(set(universe) | {p["symbol"] for p in held})
        quotes = self._request("GET", "/v2/stocks/quotes/latest", data=True,
                               params={"symbols": ",".join(symbols), "feed": "iex"})["quotes"]
        assets = {s: self._request("GET", "/v2/assets/" + urlquote(s, safe="")) for s in symbols}
        return {"account_id": account["id"], "cash": account["cash"], "equity": account["equity"],
                "positions": {p["symbol"]: p["qty"] for p in held}, "observed_at": observed_at,
                "market_open": clock.get("is_open") is True, "open_orders": opened,
                "quotes": {s: {"bid": str(q["bp"]), "ask": str(q["ap"]), "at": q["t"]}
                           for s, q in quotes.items() if q is not None},
                "assets": {s: {"tradable": a.get("tradable") is True and a.get("class") == "us_equity"}
                           for s, a in assets.items()}}

    def account_id(self):
        return self._request("GET", "/v2/account")["id"]

    def lookup(self, client_order_id):
        return self._request("GET", "/v2/orders:by_client_order_id", absent_ok=True,
                             params={"client_order_id": client_order_id})

    def submit(self, order):
        return self._request("POST", "/v2/orders", json=order)

    def cancel(self, broker_order_id):
        return self._request("DELETE", "/v2/orders/" + urlquote(broker_order_id, safe=""))
