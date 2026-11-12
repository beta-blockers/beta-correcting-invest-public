"""Serial, durable paper submissions with explicit resume and cancellation."""
from __future__ import annotations

from .common import decimal, digest, loads, now, require, timestamp
from .planning import Limits, account_ok, positions, quote

TERMINAL = {"filled", "canceled", "expired", "rejected"}
PENDING = {"new", "accepted", "pending_new", "partially_filled", "pending_cancel", "accepted_for_bidding"}


def client_id(identity, index):
    return f"ppe-{identity[:32]}-{index}"


def validate_observation(observation, order, coid, previous=None):
    require(isinstance(observation, dict) and observation.get("client_order_id") == coid,
            "Broker order identity mismatch")
    for key in ("symbol", "side", "type", "time_in_force"):
        require(observation.get(key) == order[key], "Broker order contract mismatch")
    require(decimal(observation.get("qty")) == decimal(order["qty"]) and
            decimal(observation.get("limit_price")) == decimal(order["limit_price"]) and
            observation.get("extended_hours") is False, "Broker order terms changed")
    require(isinstance(observation.get("id"), str) and observation["id"], "Missing broker order ID")
    status = observation.get("status")
    require(status in TERMINAL | PENDING, "Unknown or externally replaced broker order; inspect manually")
    filled = decimal(observation.get("filled_qty"))
    require(0 <= filled <= decimal(order["qty"]), "Invalid broker fill quantity")
    if previous:
        require(observation["id"] == previous["id"] and filled >= decimal(previous["filled_qty"]),
                "Broker order identity or fill history regressed")
        if previous["status"] in TERMINAL:
            require(status == previous["status"], "Terminal broker order status changed")
    if filled:
        price = decimal(observation.get("filled_avg_price"))
        limit = decimal(order["limit_price"])
        require(price > 0 and (price <= limit if order["side"] == "buy" else price >= limit),
                "Broker fill violates the limit price")
    require(status != "filled" or filled == decimal(order["qty"]), "Incomplete fill marked filled")
    require(status != "rejected" or filled == 0, "Rejected order carries a fill")
    return status, filled


def execute(store, identity, broker, trust, *, clock=now):
    instant = clock()
    plan, state = store.plan(identity)
    require(not plan["offline"], "Offline previews cannot execute")
    require(broker.account_id() == plan["account_id"], "Paper account binding changed")
    if state in ("complete", "canceled", "halted"):
        return {"plan_id": identity, "status": state}
    require(not store.outstanding(identity), "Another plan has unresolved submissions")
    payload, _ = store.load_package(plan["package_id"], trust, instant, check_freshness=False)
    require(payload["purpose"] == "paper", "Demonstration packages cannot submit broker orders")
    limits = Limits(**plan["limits"])
    limits.validate()
    expected = dict(plan["starting_positions"])
    for index, order in enumerate(plan["orders"]):
        record = store.order(identity, index)
        coid = client_id(identity, index)
        if record["attempted"]:
            observed = broker.lookup(coid)
            require(observed is not None,
                    "Submission outcome is uncertain; no retry. Inspect broker history manually")
        else:
            instant = clock()
            # Resume may observe old orders after expiry, but must never place a new one.
            fresh, _ = store.load_package(plan["package_id"], trust, instant)
            require(digest(fresh) == plan["package_sha256"], "Research changed; preview a new plan")
            require(0 <= (instant - timestamp(plan["created_at"])).total_seconds() <= limits.plan_max_age_seconds,
                    "Plan expired; cancel/reconcile before creating a fresh plan")
            if "activation" in plan:
                require(instant < timestamp(plan["activation"]["valid_until"])
                        and order["symbol"] in plan["activation"]["symbols"]
                        and order["side"] == plan["activation"]["sides"][order["symbol"]]
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
            require(positions(snapshot) == {s: q for s, q in expected.items() if q},
                    "Positions changed outside this plan; stop and reconcile")
            require(not snapshot["open_orders"], "An open broker order blocks the next submission")
            bid, ask = quote(snapshot, order["symbol"], instant, limits)
            price = decimal(order["limit_price"])
            amount = price * decimal(order["qty"])
            require(amount <= decimal(limits.max_order_usd), "Order exceeds limit")
            if order["side"] == "buy":
                require(ask <= price and amount <= decimal(snapshot["cash"]),
                        "Quote moved beyond the limit or observed cash is insufficient")
            else:
                require(bid >= price and decimal(order["qty"]) <= expected.get(order["symbol"], 0),
                        "Quote moved beyond the limit or sell would exceed holdings")
            # A pre-existing ID cannot silently become this run's first submission.
            require(broker.lookup(coid) is None, "Client order ID already exists before recorded submission")
            store.status(identity, "started")
            store.mark_attempt(identity, index)
            broker.submit({**order, "client_order_id": coid})
            observed = broker.lookup(coid)
            require(observed is not None, "Submission awaits reconciliation; never resend it")
        previous = loads(record["observation"]) if record["observation"] else None
        status, filled = validate_observation(observed, order, coid, previous)
        store.record(identity, index, observed)
        if status != "filled":
            if status in TERMINAL:
                store.status(identity, "halted")
                return {"plan_id": identity, "status": "halted", "order_status": status,
                        "next_step": "Inspect fills and create a fresh preview"}
            return {"plan_id": identity, "status": "pending", "client_order_id": coid,
                    "next_step": "Run execute again to reconcile, or cancel this plan"}
        expected[order["symbol"]] = expected.get(order["symbol"], 0) + int(filled) * (1 if order["side"] == "buy" else -1)
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
        coid = client_id(identity, index)
        observed = broker.lookup(coid)
        require(observed is not None, "Cannot cancel an uncertain submission; inspect broker history manually")
        previous = loads(record["observation"]) if record["observation"] else None
        status, _ = validate_observation(observed, order, coid, previous)
        if status not in TERMINAL:
            broker.cancel(observed["id"])
            updated = broker.lookup(coid)
            require(updated is not None, "Cancellation awaits reconciliation")
            status, _ = validate_observation(updated, order, coid, observed)
            observed = updated
        pending |= status not in TERMINAL
        store.record(identity, index, observed)
    store.status(identity, "started" if pending else "canceled")
    return {"plan_id": identity, "status": "cancel_pending" if pending else "canceled"}
