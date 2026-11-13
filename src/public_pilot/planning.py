"""Completed target weights -> bounded whole-share paper orders."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

from .common import decimal, digest, fields, iso, require, timestamp


@dataclass(frozen=True)
class Limits:
    allocation_usd: str = "1000"
    max_order_usd: str = "250"  # library default; the command line's is cli.DEFAULT_MAX_ORDER
    max_turnover_usd: str = "1000"
    max_position_weight: str = "0.5"
    collar_bps: int = 25
    max_spread_bps: int = 50
    quote_max_age_seconds: int = 60
    plan_max_age_seconds: int = 120

    def validate(self):
        for name in ("allocation_usd", "max_order_usd", "max_turnover_usd"):
            require(0 < decimal(getattr(self, name)) <= 1_000_000, "Invalid dollar limit")
        require(0 < decimal(self.max_position_weight) <= 1, "Invalid concentration limit")
        for name, ceiling in (("collar_bps", 100), ("max_spread_bps", 100),
                              ("quote_max_age_seconds", 120), ("plan_max_age_seconds", 300)):
            require(type(getattr(self, name)) is int and 0 < getattr(self, name) <= ceiling,
                    "Invalid execution freshness or price limit")


def quote(snapshot, symbol, instant, limits):
    raw = snapshot["quotes"].get(symbol)
    require(isinstance(raw, dict), f"{symbol}: Missing quote")
    bid, ask = decimal(raw["bid"]), decimal(raw["ask"])
    require(0 < bid <= ask, f"{symbol}: Invalid or crossed quote")
    age = (instant - timestamp(raw["at"])).total_seconds()
    require(0 <= age <= limits.quote_max_age_seconds, f"{symbol}: Stale or future quote")
    require((ask - bid) / ((ask + bid) / 2) * 10_000 <= limits.max_spread_bps,
            f"{symbol}: Quote spread exceeds limit")
    require(snapshot["assets"].get(symbol, {}).get("tradable") is True, f"{symbol}: Asset is not tradable")
    return bid, ask


def positions(snapshot):
    result = {}
    for symbol, raw in snapshot["positions"].items():
        qty = decimal(raw)
        require(qty >= 0 and qty == qty.to_integral_value(),
                f"{symbol}: Only long, whole-share positions are supported")
        if qty:
            result[symbol] = int(qty)
    return result


def order_symbols(orders):
    """The symbols of broker orders, for naming them in a refusal."""
    names = sorted({str(o["symbol"]) for o in orders if isinstance(o, dict) and o.get("symbol")})
    return f": {', '.join(names)}" if names else ""


def account_ok(snapshot, instant):
    require(isinstance(snapshot["account_id"], str) and snapshot["account_id"], "Missing account binding")
    require(snapshot["market_open"] is True, "Regular market session is closed")
    require(0 <= (instant - timestamp(snapshot["observed_at"])).total_seconds() <= 30,
            "Account observation is stale")
    require(decimal(snapshot["cash"]) >= 0 and decimal(snapshot["equity"]) > 0,
            "Cash-funded account required")


def build_plan(payload, snapshot, limits, instant, *, offline=False, activation=None):
    limits.validate()
    account_ok(snapshot, instant)
    require(not snapshot["open_orders"],
            "Resolve existing broker orders before planning" + order_symbols(snapshot["open_orders"]))
    held = positions(snapshot)
    foreign = sorted(set(held) - set(payload["universe"]))
    require(not foreign, f"Foreign positions outside this research universe: {', '.join(foreign)}")
    concentrated = sorted(s for s, w in payload["targets"].items()
                          if decimal(w) > decimal(limits.max_position_weight))
    require(not concentrated, f"Research exceeds the customer's concentration limit: {', '.join(concentrated)}")
    allocation = min(decimal(limits.allocation_usd), decimal(snapshot["equity"]))
    active = set(payload["universe"])
    if activation is not None:
        fields(activation, ("package_sha256", "symbols", "sides", "valid_until", "decision_sha256"))
        require(activation["package_sha256"] == digest(payload), "Activation belongs to different research")
        selected = activation["symbols"]
        require(isinstance(selected, list) and all(isinstance(s, str) for s in selected)
                and len(set(selected)) == len(selected) and set(selected) <= active,
                "Invalid activation symbols")
        require(instant < timestamp(activation["valid_until"]), "Activation expired")
        require(isinstance(activation["decision_sha256"], str) and
                len(activation["decision_sha256"]) == 64 and
                all(c in "0123456789abcdef" for c in activation["decision_sha256"]),
                "Missing activation decision identity")
        active = set(selected)
        require(isinstance(activation["sides"], dict) and set(activation["sides"]) == active
                and all(s in ("buy", "sell") for s in activation["sides"].values()),
                "Invalid activation directions")
    collar = Decimal(limits.collar_bps) / 10_000
    orders, desired = [], {}
    for symbol in sorted(set(held) | set(payload["targets"])):
        if symbol not in active:
            desired[symbol] = held.get(symbol, 0)
            continue
        bid, ask = quote(snapshot, symbol, instant, limits)
        buy_price = ask * (1 + collar)
        buy_price = buy_price.quantize(Decimal("0.01") if buy_price >= 1 else Decimal("0.0001"), rounding=ROUND_CEILING)
        target = int(allocation * decimal(payload["targets"].get(symbol, "0")) / buy_price)
        desired[symbol] = target
        change = target - held.get(symbol, 0)
        if not change:
            continue
        side = "buy" if change > 0 else "sell"
        if activation is not None and side != activation["sides"][symbol]:
            desired[symbol] = held.get(symbol, 0)
            continue
        price = buy_price if side == "buy" else bid * (1 - collar)
        if side == "sell":
            price = price.quantize(Decimal("0.01") if price >= 1 else Decimal("0.0001"), rounding=ROUND_FLOOR)
        require(price > 0, f"{symbol}: Price collar rounds to zero")
        chunk = int(decimal(limits.max_order_usd) / price)
        require(chunk > 0, f"{symbol}: One share exceeds the per-order limit "
                           f"(limit price {price} USD, per-order limit {limits.max_order_usd} USD)")
        remaining = abs(change)
        while remaining:
            qty = min(remaining, chunk)
            orders.append({"symbol": symbol, "side": side, "qty": str(qty), "type": "limit",
                           "time_in_force": "day", "limit_price": str(price), "extended_hours": False})
            remaining -= qty
            require(len(orders) <= 100, "Plan exceeds 100 child orders")
    orders.sort(key=lambda o: (o["side"] != "sell", o["symbol"]))
    turnover = sum(decimal(o["qty"]) * decimal(o["limit_price"]) for o in orders)
    require(turnover <= decimal(limits.max_turnover_usd), "Plan exceeds the turnover limit")
    sells = sum(decimal(o["qty"]) * decimal(o["limit_price"]) for o in orders if o["side"] == "sell")
    buys = sum(decimal(o["qty"]) * decimal(o["limit_price"]) for o in orders if o["side"] == "buy")
    require(buys <= decimal(snapshot["cash"]) + sells, "Insufficient cash at conservative limit prices")
    plan = {"format": "public-pilot-plan-v1", "package_id": payload["package_id"],
            "package_sha256": digest(payload), "edition_id": payload["edition_id"],
            "account_id": snapshot["account_id"], "created_at": iso(instant),
            "offline": offline, "limits": asdict(limits), "starting_positions": held,
            "desired_positions": desired, "allocation_usd": str(allocation), "orders": orders}
    if activation is not None:
        plan["activation"] = activation
    return plan
