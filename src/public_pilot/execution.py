"""Serial, durable paper submissions with explicit resume and cancellation."""
from __future__ import annotations

from .broker import OrderRejected
from .common import decimal, digest, loads, now, require, timestamp
from .planning import Limits, account_ok, order_symbols, positions, quote

TERMINAL = {"filled", "canceled", "expired", "rejected"}
PENDING = {"new", "accepted", "pending_new", "partially_filled", "pending_cancel", "accepted_for_bidding"}
# Recorded for a submission that the broker rejected outright, creating no order. Never a broker order status.
REJECTED = "submission_rejected"


def client_id(identity, index):
    return f"ppe-{identity[:32]}-{index}"


def unresolved(symbol, previous):
    """The refusal for an attempted order that the broker cannot find. A failed lookup never proves that no order
    was created: only the broker showing the order, or rejecting its submission outright, resolves it."""
    if previous:
        return f"{symbol}: The broker no longer finds an order it reported; inspect broker history manually"
    return f"{symbol}: Submission outcome is uncertain; no retry. Inspect broker history manually"


def validate_observation(observation, order, coid, previous=None):
    symbol = order["symbol"]
    require(isinstance(observation, dict) and observation.get("client_order_id") == coid,
            f"{symbol}: Broker order identity mismatch")
    for key in ("symbol", "side", "type", "time_in_force"):
        require(observation.get(key) == order[key], f"{symbol}: Broker order contract mismatch")
    require(decimal(observation.get("qty")) == decimal(order["qty"]) and
            decimal(observation.get("limit_price")) == decimal(order["limit_price"]) and
            observation.get("extended_hours") is False, f"{symbol}: Broker order terms changed")
    require(isinstance(observation.get("id"), str) and observation["id"], f"{symbol}: Missing broker order ID")
    status = observation.get("status")
    require(status in TERMINAL | PENDING, f"{symbol}: Unknown or externally replaced broker order; inspect manually")
    filled = decimal(observation.get("filled_qty"))
    require(0 <= filled <= decimal(order["qty"]), f"{symbol}: Invalid broker fill quantity")
    if previous:
        require(observation["id"] == previous["id"] and filled >= decimal(previous["filled_qty"]),
                f"{symbol}: Broker order identity or fill history regressed")
        if previous["status"] in TERMINAL:
            require(status == previous["status"], f"{symbol}: Terminal broker order status changed")
    if filled:
        price = decimal(observation.get("filled_avg_price"))
        limit = decimal(order["limit_price"])
        require(price > 0 and (price <= limit if order["side"] == "buy" else price >= limit),
                f"{symbol}: Broker fill violates the limit price")
    require(status != "filled" or filled == decimal(order["qty"]), f"{symbol}: Incomplete fill marked filled")
    require(status != "rejected" or filled == 0, f"{symbol}: Rejected order carries a fill")
    return status, filled


def execute(store, identity, broker, trust, *, clock=now):
    instant = clock()
    plan, state = store.plan(identity)
    require(not plan["offline"], "Offline previews cannot execute")
    require(broker.account_id() == plan["account_id"], "Paper account binding changed")
    if state in ("complete", "canceled", "halted"):
        return {"plan_id": identity, "status": state}
    require(not store.outstanding(identity), "Another plan has unresolved submissions")
    # Every key in the chain must allow paper, for demo and paper editions alike.
    payload, _ = store.load_package(plan["package_id"], trust, instant, check_freshness=False, trading=True)
    limits = Limits(**plan["limits"])
    limits.validate()
    expected = dict(plan["starting_positions"])
    for index, order in enumerate(plan["orders"]):
        symbol = order["symbol"]
        record = store.order(identity, index)
        coid = client_id(identity, index)
        previous = loads(record["observation"]) if record["observation"] else None
        if record["attempted"]:
            # A verified complete fill is final, so only unfinished orders are looked up again.
            observed = previous if previous and previous.get("status") == "filled" else broker.lookup(coid)
            require(observed is not None, unresolved(symbol, previous))
        else:
            instant = clock()
            # Resume may observe old orders after expiry, but must never place a new one.
            fresh, _ = store.load_package(plan["package_id"], trust, instant, trading=True)
            require(digest(fresh) == plan["package_sha256"], "Research changed; preview a new plan")
            require(0 <= (instant - timestamp(plan["created_at"])).total_seconds() <= limits.plan_max_age_seconds,
                    "Plan expired; cancel/reconcile before creating a fresh plan")
            if "activation" in plan:
                require(instant < timestamp(plan["activation"]["valid_until"])
                        and symbol in plan["activation"]["symbols"]
                        and order["side"] == plan["activation"]["sides"][symbol]
                        and plan["activation"]["package_sha256"] == plan["package_sha256"],
                        "Activation expired or changed")
            # A fresh observation for this order: the account, the market session, and this stock's quote and
            # tradability, all read again before every submission.
            snapshot = broker.snapshot([symbol])
            instant = clock()
            account_ok(snapshot, instant)
            require(instant < timestamp(fresh["valid_until"]) and
                    (instant - timestamp(plan["created_at"])).total_seconds() <= limits.plan_max_age_seconds,
                    "Research or plan expired during observation")
            if "activation" in plan:
                require(instant < timestamp(plan["activation"]["valid_until"]),
                        "Activation expired during observation")
            require(snapshot["account_id"] == plan["account_id"], "Account binding changed")
            held, wanted = positions(snapshot), {s: q for s, q in expected.items() if q}
            drift = sorted(s for s in set(held) | set(wanted) if held.get(s, 0) != wanted.get(s, 0))
            require(not drift, f"Positions changed outside this plan ({', '.join(drift)}); stop and reconcile")
            require(not snapshot["open_orders"],
                    "An open broker order blocks the next submission" + order_symbols(snapshot["open_orders"]))
            bid, ask = quote(snapshot, symbol, instant, limits)
            price = decimal(order["limit_price"])
            amount = price * decimal(order["qty"])
            require(amount <= decimal(limits.max_order_usd), f"{symbol}: Order exceeds limit")
            if order["side"] == "buy":
                require(ask <= price and amount <= decimal(snapshot["cash"]),
                        f"{symbol}: Quote moved beyond the limit or observed cash is insufficient")
            else:
                require(bid >= price and decimal(order["qty"]) <= expected.get(symbol, 0),
                        f"{symbol}: Quote moved beyond the limit or sell would exceed holdings")
            # A pre-existing ID cannot silently become this run's first submission.
            require(broker.lookup(coid) is None, f"{symbol}: Client order ID already exists before recorded submission")
            store.status(identity, "started")
            # The intent is durable before the request: after a crash or a lost response, the order is looked up
            # by its client ID and never sent again.
            store.mark_attempt(identity, index)
            try:
                accepted = broker.submit({**order, "client_order_id": coid})
            except OrderRejected as exc:
                # The broker rejected the submission and created no order: settle the intent and stop this plan.
                store.reject(identity, index, {"client_order_id": coid, "symbol": symbol, "status": REJECTED,
                                               "http_status": exc.status_code, "detail": exc.detail})
                return {"plan_id": identity, "status": "halted", "order_status": REJECTED, "symbol": symbol,
                        "reason": str(exc), "next_step": "Inspect fills and create a fresh preview"}
            if isinstance(accepted, dict) and accepted.get("client_order_id") == coid:
                # The broker's answer shows that the order exists. Keep it before asking the broker anything else.
                validate_observation(accepted, order, coid)
                store.record(identity, index, accepted)
                previous = accepted
            observed = broker.lookup(coid)
            if observed is None:
                observed = previous  # accepted, but not visible to a lookup yet
            require(observed is not None, f"{symbol}: Submission awaits reconciliation; never resend it")
        status, filled = validate_observation(observed, order, coid, previous)
        store.record(identity, index, observed)
        if status != "filled":
            if status in TERMINAL:
                store.status(identity, "halted")
                return {"plan_id": identity, "status": "halted", "order_status": status, "symbol": symbol,
                        "next_step": "Inspect fills and create a fresh preview"}
            return {"plan_id": identity, "status": "pending", "client_order_id": coid, "symbol": symbol,
                    "next_step": "Run execute again to reconcile, or cancel this plan"}
        expected[symbol] = expected.get(symbol, 0) + int(filled) * (1 if order["side"] == "buy" else -1)
    store.status(identity, "complete")
    return {"plan_id": identity, "status": "complete"}


def cancel(store, identity, broker):
    plan, state = store.plan(identity)
    require(not plan["offline"], "Offline previews have no broker orders")
    require(broker.account_id() == plan["account_id"], "Paper account binding changed")
    if state in ("complete", "canceled", "halted"):
        return {"plan_id": identity, "status": state}
    pending = False
    for index, order in enumerate(plan["orders"]):
        record = store.order(identity, index)
        if not record["attempted"]:
            continue
        symbol = order["symbol"]
        coid = client_id(identity, index)
        previous = loads(record["observation"]) if record["observation"] else None
        if previous and previous.get("status") in TERMINAL | {REJECTED}:
            continue  # nothing is left to cancel, and a final record is not looked up again
        observed = broker.lookup(coid)
        require(observed is not None, unresolved(symbol, previous))
        status, _ = validate_observation(observed, order, coid, previous)
        # Keep what the broker reported before asking it to cancel.
        store.record(identity, index, observed)
        if status not in TERMINAL:
            broker.cancel(observed["id"])
            updated = broker.lookup(coid)
            require(updated is not None, f"{symbol}: Cancellation awaits reconciliation")
            status, _ = validate_observation(updated, order, coid, observed)
            store.record(identity, index, updated)
        pending |= status not in TERMINAL
    store.status(identity, "started" if pending else "canceled")
    return {"plan_id": identity, "status": "cancel_pending" if pending else "canceled"}
