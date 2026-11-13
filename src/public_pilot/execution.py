"""Serial, durable paper submissions with explicit resume and cancellation."""
from __future__ import annotations

from datetime import timedelta

from .broker import BrokerRefused
from .common import decimal, digest, iso, loads, now, require, timestamp
from .planning import Limits, account_ok, order_symbols, positions, quote

TERMINAL = {"filled", "canceled", "expired", "rejected"}
PENDING = {"new", "accepted", "pending_new", "partially_filled", "pending_cancel", "accepted_for_bidding"}
# Recorded for submissions that never became broker orders; neither is ever a broker status.
REFUSED = "submission_refused"  # the broker answered the submission with a refusal
NEVER_PLACED = "never_placed"  # no answer, and the broker still had no order long after it could have arrived
# A submission starts only while its plan is fresh. This long after that window, a submission that the broker
# still has no order for under its client ID never reached it.
SETTLE_SECONDS = 300


def client_id(identity, index):
    return f"ppe-{identity[:32]}-{index}"


def settled_at(plan):
    """From when an unanswered submission of this plan counts as never placed if the broker cannot find it."""
    limits = Limits(**plan["limits"])
    limits.validate()
    return timestamp(plan["created_at"]) + timedelta(seconds=limits.plan_max_age_seconds + SETTLE_SECONDS)


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
            require(observed is not None,
                    f"{symbol}: Submission outcome is uncertain; no retry. Inspect broker history manually. "
                    f"From {iso(settled_at(plan))}, cancel-paper closes this plan without resending the order")
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
            snapshot = broker.snapshot(payload["universe"])
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
                broker.submit({**order, "client_order_id": coid})
            except BrokerRefused as exc:
                # The broker answered and refused, so no order exists: settle the intent and stop this plan.
                store.refuse(identity, index, {"client_order_id": coid, "symbol": symbol, "status": REFUSED,
                                               "http_status": exc.status_code, "detail": exc.detail})
                return {"plan_id": identity, "status": "halted", "order_status": REFUSED, "symbol": symbol,
                        "reason": str(exc), "next_step": "Inspect fills and create a fresh preview"}
            observed = broker.lookup(coid)
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


def cancel(store, identity, broker, *, clock=now):
    instant = clock()
    plan, state = store.plan(identity)
    require(not plan["offline"], "Offline previews have no broker orders")
    require(broker.account_id() == plan["account_id"], "Paper account binding changed")
    if state in ("complete", "canceled", "halted"):
        return {"plan_id": identity, "status": state}
    pending, never_placed = False, []
    for index, order in enumerate(plan["orders"]):
        record = store.order(identity, index)
        if not record["attempted"]:
            continue
        symbol = order["symbol"]
        coid = client_id(identity, index)
        previous = loads(record["observation"]) if record["observation"] else None
        if previous and previous.get("status") in TERMINAL | {REFUSED, NEVER_PLACED}:
            continue  # nothing is left to cancel, and a final record is not looked up again
        observed = broker.lookup(coid)
        if observed is None:
            # The broker has no order under this client ID. One it reported earlier and lost needs a person.
            require(previous is None,
                    f"{symbol}: The broker no longer finds an order it reported; inspect broker history manually")
            # It never answered the submission. Once no submission of this plan could still arrive, the order
            # was never placed: close the plan without ever sending it again.
            settle = settled_at(plan)
            require(instant >= settle,
                    f"{symbol}: Cannot cancel an uncertain submission yet: the broker has no order under its "
                    f"client ID. Run cancel-paper again from {iso(settle)} to close this plan without resending it")
            store.record(identity, index, {"client_order_id": coid, "symbol": symbol, "status": NEVER_PLACED,
                                           "checked_at": iso(instant)})
            never_placed.append({"symbol": symbol, "client_order_id": coid})
            continue
        status, _ = validate_observation(observed, order, coid, previous)
        if status not in TERMINAL:
            broker.cancel(observed["id"])
            updated = broker.lookup(coid)
            require(updated is not None, f"{symbol}: Cancellation awaits reconciliation")
            status, _ = validate_observation(updated, order, coid, observed)
            observed = updated
        pending |= status not in TERMINAL
        store.record(identity, index, observed)
    store.status(identity, "started" if pending else "canceled")
    result = {"plan_id": identity, "status": "cancel_pending" if pending else "canceled"}
    if never_placed:
        result["never_placed"] = never_placed
    return result
