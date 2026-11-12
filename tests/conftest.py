import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from public_pilot.common import Refused, canonical, digest, iso
from public_pilot.packages import FORMAT
from public_pilot.planning import Limits, build_plan
from public_pilot.state import Store

AT = datetime(2030, 1, 2, 15, tzinfo=timezone.utc)


@pytest.fixture
def author():
    # Ephemeral synthetic test identity; no publisher private key is shipped.
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    trust = {"test-key": {"public_key": base64.b64encode(public).decode(), "author_id": "test-author",
                          "packages": ["test-research"], "allow_paper": True}}

    def sign(payload, kind="snapshot"):
        body = {"format": FORMAT, "kind": kind, "key_id": "test-key", "payload": deepcopy(payload)}
        return {**body, "signature": base64.b64encode(private.sign(canonical(body))).decode()}

    return trust, sign


@pytest.fixture
def payload():
    return {"package_id": "test-research", "edition_id": "edition-1", "author_id": "test-author",
            "engine_major": 1, "purpose": "paper", "published_at": iso(AT - timedelta(days=2)),
            "information_cutoff": iso(AT - timedelta(days=3)), "valid_until": iso(AT + timedelta(days=30)),
            "geographies": ["TEST"], "policy_ids": ["synthetic-policy"], "universe": ["DEMOA", "DEMOB"],
            "targets": {"DEMOA": "0.4", "DEMOB": "0.4"}, "research": "Synthetic test research.", "evidence": []}


@pytest.fixture
def snapshot():
    return {"account_id": "paper-test-account", "cash": "1000", "equity": "1000", "positions": {},
            "observed_at": iso(AT), "market_open": True, "open_orders": [],
            "quotes": {s: {"bid": "99.9", "ask": "100", "at": iso(AT)} for s in ("DEMOA", "DEMOB")},
            "assets": {s: {"tradable": True} for s in ("DEMOA", "DEMOB")}}


@pytest.fixture
def store(tmp_path):
    result = Store(tmp_path / "state")
    yield result
    result.close()


def delta_for(old, **replacements):
    new = {**old, **replacements}
    return {"package_id": old["package_id"], "base_sha256": digest(old),
            "result_sha256": digest(new), "replace": replacements}


class FakeBroker:
    def __init__(self, snapshot):
        self.data = deepcopy(snapshot)
        self.orders = {}
        self.posts = 0
        self.fill_on_submit = True
        self.lose_response = False
        self.accept_before_loss = True

    def account_id(self):
        return self.data["account_id"]

    def snapshot(self, _):
        result = deepcopy(self.data)
        result["open_orders"] = [deepcopy(o) for o in self.orders.values() if o["status"] not in {"filled", "canceled"}]
        return result

    def lookup(self, coid):
        return deepcopy(self.orders.get(coid))

    def submit(self, order):
        self.posts += 1
        if self.lose_response and not self.accept_before_loss:
            raise Refused("Connection lost before broker outcome is known")
        coid = order["client_order_id"]
        assert coid not in self.orders
        self.orders[coid] = {**order, "id": "broker-" + coid, "status": "accepted",
                             "filled_qty": "0", "filled_avg_price": None}
        if self.fill_on_submit:
            self.fill(coid)
        if self.lose_response:
            self.lose_response = False
            raise Refused("Response lost after broker acceptance")
        return deepcopy(self.orders[coid])

    def fill(self, coid):
        order = self.orders[coid]
        qty, price = Decimal(order["qty"]), Decimal(order["limit_price"])
        sign = 1 if order["side"] == "buy" else -1
        self.data["positions"][order["symbol"]] = str(Decimal(self.data["positions"].get(order["symbol"], "0")) + sign * qty)
        self.data["cash"] = str(Decimal(self.data["cash"]) - sign * qty * price)
        order.update(status="filled", filled_qty=order["qty"], filled_avg_price=str(price))

    def cancel(self, broker_id):
        for order in self.orders.values():
            if order["id"] == broker_id:
                order["status"] = "canceled"


@pytest.fixture
def prepared(store, author, payload, snapshot):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    plan = build_plan(payload, snapshot, Limits(), AT)
    identity = store.save_plan(plan)
    return identity, FakeBroker(snapshot)
