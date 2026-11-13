"""Reader recovery after a publisher key is removed: a snapshot signed with a trusted key replaces the installed
edition, the downgrade checks still apply, and plans and order records stay in the state directory."""
import base64
from copy import deepcopy
from datetime import timedelta
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from conftest import AT, FakeBroker, delta_for
from public_pilot import cli
from public_pilot.common import Refused, canonical, iso, loads
from public_pilot.execution import execute
from public_pilot.packages import FORMAT
from public_pilot.planning import Limits, build_plan

LATER = AT + timedelta(days=60)
MODES = [(False, AT), (True, AT), (True, LATER)]


@pytest.fixture
def replacement():
    """The author's replacement key, and the reader's trust file after removing the old key."""
    private = Ed25519PrivateKey.generate()
    public = base64.b64encode(private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()
    trust = {"new-key": {"public_key": public, "author_id": "test-author", "packages": ["test-research"],
                         "allow_paper": True}}

    def sign(payload, kind="snapshot"):
        body = {"format": FORMAT, "kind": kind, "key_id": "new-key", "payload": deepcopy(payload)}
        return {**body, "signature": base64.b64encode(private.sign(canonical(body))).decode()}

    return trust, sign


def newer(payload, edition_id="edition-2", **changes):
    return {**payload, "edition_id": edition_id, "published_at": iso(AT - timedelta(days=1)), **changes}


def rows(store, table):
    return [dict(row) for row in store.db.execute(f"SELECT * FROM {table} ORDER BY 1, 2")]


def stored_key_ids(store, edition_id):
    row = store.db.execute("SELECT proofs FROM editions WHERE edition_id=?", (edition_id,)).fetchone()
    return [envelope["key_id"] for envelope in loads(row["proofs"])]


@pytest.mark.parametrize("allow_expired, instant", MODES)
def test_a_newer_snapshot_with_the_new_key_replaces_an_edition_whose_key_was_removed(
        store, author, replacement, payload, allow_expired, instant):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    with pytest.raises(Refused, match="not in the local trust store"):
        store.load_package(payload["package_id"], new_trust, instant, check_freshness=False)
    assert store.install(new_sign(newer(payload)), new_trust, instant, allow_expired=allow_expired) == newer(payload)
    assert store.load_package(payload["package_id"], new_trust, instant, check_freshness=False)[0] == newer(payload)
    assert stored_key_ids(store, "edition-2") == ["new-key"]


@pytest.mark.parametrize("allow_expired, instant", MODES)
def test_the_same_edition_re_signed_with_the_new_key_replaces_only_its_proofs(
        store, author, replacement, payload, allow_expired, instant):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    hash_before = rows(store, "editions")[0]["hash"]
    assert store.install(new_sign(payload), new_trust, instant, allow_expired=allow_expired) == payload
    assert store.load_package(payload["package_id"], new_trust, instant, check_freshness=False)[0] == payload
    assert stored_key_ids(store, "edition-1") == ["new-key"]
    assert [row["hash"] for row in rows(store, "editions")] == [hash_before]
    assert rows(store, "active") == [{"package_id": "test-research", "edition_id": "edition-1"}]


def test_while_the_old_key_is_still_trusted_reinstalling_changes_nothing(store, author, replacement, payload):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    both = {**old_trust, **new_trust}
    assert store.install(new_sign(payload), both, AT) == payload
    assert stored_key_ids(store, "edition-1") == ["test-key"]


def rotated(old_trust, new_trust):
    """Trust as catalog trust writes it after a key rotation: the retired key still verifies, only the new trades."""
    return {"test-key": {**old_trust["test-key"], "allow_paper": False}, **new_trust}


@pytest.mark.parametrize("purpose", ["demo", "paper"])
def test_the_edition_re_signed_after_a_key_rotation_can_trade_again(store, author, replacement, payload, snapshot,
                                                                    purpose):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    payload["purpose"] = purpose
    store.install(old_sign(payload), old_trust, AT)
    plan = store.save_plan(build_plan(payload, snapshot, Limits(), AT))
    trust = rotated(old_trust, new_trust)
    with pytest.raises(Refused, match="trusted only for demonstrations"):
        execute(store, plan, FakeBroker(snapshot), trust, clock=lambda: AT)
    assert store.install(new_sign(payload), trust, AT) == payload
    assert stored_key_ids(store, "edition-1") == ["new-key"]
    assert execute(store, plan, FakeBroker(snapshot), trust, clock=lambda: AT)["status"] == "complete"


def test_an_old_copy_never_replaces_proofs_that_can_trade(store, author, replacement, payload):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    payload["purpose"] = "demo"
    trust = rotated(old_trust, new_trust)
    store.install(new_sign(payload), trust, AT)
    assert store.install(old_sign(payload), trust, AT) == payload  # it still verifies for reading
    assert stored_key_ids(store, "edition-1") == ["new-key"]


@pytest.mark.parametrize("allow_expired, instant", MODES)
def test_downgrade_and_identity_checks_still_apply_after_the_key_was_removed(
        store, author, replacement, payload, allow_expired, instant):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(newer(payload)), old_trust, AT)
    proofs_before = rows(store, "editions")
    other_author = {"new-key": {**new_trust["new-key"], "author_id": "other-author"}}
    refusals = [
        (new_sign(payload), new_trust, "downgrade"),
        (new_sign(newer(payload, "edition-3", published_at=iso(AT - timedelta(hours=1)),
                        information_cutoff=iso(AT - timedelta(days=4)))), new_trust, "downgrade"),
        (new_sign(newer(payload, "edition-4", published_at=iso(AT - timedelta(hours=1)), purpose="demo")),
         new_trust, "identity change"),
        (new_sign(newer(payload, "edition-5", published_at=iso(AT - timedelta(hours=1)), author_id="other-author")),
         other_author, "identity change"),
        (new_sign(newer(payload, published_at=iso(AT - timedelta(hours=1)), research="Rewritten.")),
         new_trust, "Existing edition cannot be replaced"),
    ]
    for envelope, trust, message in refusals:
        with pytest.raises(Refused, match=message):
            store.install(envelope, trust, instant, allow_expired=allow_expired)
    assert rows(store, "editions") == proofs_before
    assert store.installed(payload["package_id"]) == newer(payload)


def test_the_replacement_itself_must_verify_with_the_current_trust(store, author, replacement, payload):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    with pytest.raises(Refused, match="not in the local trust store"):
        store.install(old_sign(newer(payload)), new_trust, AT)
    forged = new_sign(newer(payload))
    forged["payload"]["targets"] = {"DEMOA": "0.8"}
    with pytest.raises(Refused, match="signature"):
        store.install(forged, new_trust, AT)
    with pytest.raises(Refused, match="Expired"):
        store.install(new_sign(newer(payload)), new_trust, LATER)
    assert store.installed(payload["package_id"]) == payload


def test_a_delta_cannot_build_on_an_edition_whose_key_was_removed(store, author, replacement, payload):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    delta = delta_for(payload, edition_id="edition-2", published_at=iso(AT - timedelta(days=1)))
    with pytest.raises(Refused, match="not in the local trust store"):
        store.install(new_sign(delta, "delta"), new_trust, AT)
    assert stored_key_ids(store, "edition-1") == ["test-key"]


def test_an_installed_delta_chain_is_replaced_by_the_full_snapshot(store, author, replacement, payload):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    delta = delta_for(payload, edition_id="edition-2", published_at=iso(AT - timedelta(days=1)))
    store.install(old_sign(delta, "delta"), old_trust, AT)
    assert stored_key_ids(store, "edition-2") == ["test-key", "test-key"]
    assert store.installed(payload["package_id"]) == newer(payload)
    assert store.install(new_sign(newer(payload)), new_trust, AT) == newer(payload)
    assert stored_key_ids(store, "edition-2") == ["new-key"]


@pytest.mark.parametrize("damage", ["hash", "proofs"])
def test_a_damaged_installed_record_is_still_refused(store, author, replacement, payload, damage):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    if damage == "hash":
        store.db.execute("UPDATE editions SET hash=?", ("0" * 64,))
    else:
        store.db.execute("UPDATE editions SET proofs=?", ('[{"payload": "not an object"}]',))
    with pytest.raises(Refused, match="Installed package identity changed"):
        store.install(new_sign(newer(payload)), new_trust, AT)


def test_plans_and_order_records_survive_and_old_plans_never_trade_on_new_research(
        store, author, replacement, payload, snapshot):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    executed = store.save_plan(build_plan(payload, snapshot, Limits(), AT))
    broker = FakeBroker(snapshot)
    assert execute(store, executed, broker, old_trust, clock=lambda: AT)["status"] == "complete"
    pending_plan = build_plan(payload, snapshot, Limits(max_order_usd="200"), AT)
    assert pending_plan["orders"]
    pending = store.save_plan(pending_plan)
    plans, orders, posts = rows(store, "plans"), rows(store, "orders"), broker.posts
    assert orders and all(order["attempted"] == 1 and order["observation"] for order in orders)

    store.install(new_sign(newer(payload)), new_trust, AT)
    assert (rows(store, "plans"), rows(store, "orders")) == (plans, orders)
    assert execute(store, executed, broker, new_trust, clock=lambda: AT)["status"] == "complete"
    with pytest.raises(Refused, match="Research changed; preview a new plan"):
        execute(store, pending, broker, new_trust, clock=lambda: AT)
    assert broker.posts == posts


def test_a_plan_made_from_the_same_edition_still_matches_after_it_is_re_signed(
        store, author, replacement, payload, snapshot):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    store.install(old_sign(payload), old_trust, AT)
    plan = store.save_plan(build_plan(payload, snapshot, Limits(), AT))
    with pytest.raises(Refused, match="not in the local trust store"):
        execute(store, plan, FakeBroker(snapshot), new_trust, clock=lambda: AT)
    store.install(new_sign(payload), new_trust, AT)
    assert execute(store, plan, FakeBroker(snapshot), new_trust, clock=lambda: AT)["status"] == "complete"


def test_the_documented_reader_recovery_works_from_the_command_line(tmp_path, author, replacement, payload,
                                                                     monkeypatch, capsys):
    old_trust, old_sign = author
    new_trust, new_sign = replacement
    monkeypatch.setattr(cli, "now", lambda: AT)

    def write(name, document):
        (tmp_path / name).write_text(json.dumps(document))
        return str(tmp_path / name)

    def run(trust, *argv):
        code = cli.main(["--state", str(tmp_path / "state"), "--trust", trust, *argv])
        captured = capsys.readouterr()
        return code, json.loads(captured.out if code == 0 else captured.err)

    old, new = write("old-trust.json", old_trust), write("new-trust.json", new_trust)
    assert run(old, "install", write("edition-1.json", old_sign(payload)))[0] == 0
    assert run(new, "show", "test-research") == (2, {"status": "refused",
                                                     "reason": "Publisher is not in the local trust store"})
    code, output = run(new, "install", write("edition-2.json", new_sign(newer(payload))))
    assert code == 0 and output["status"] == "installed" and output["edition_id"] == "edition-2"
    assert run(new, "show", "test-research")[1]["edition_id"] == "edition-2"
    code, refusal = run(new, "install", write("old-again.json", new_sign(payload)))
    assert code == 2 and "downgrade" in refusal["reason"]
