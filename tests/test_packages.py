from copy import deepcopy
from datetime import timedelta

import pytest

from public_pilot.common import Refused, digest, iso, loads
from public_pilot.packages import resolve_chain
from conftest import AT, delta_for


def test_tampering_fails_signature(author, payload):
    trust, sign = author
    envelope = sign(payload)
    envelope["payload"]["targets"]["DEMOA"] = "0.5"
    with pytest.raises(Refused, match="signature"):
        resolve_chain([envelope], trust, AT)


@pytest.mark.parametrize("change", [
    {"engine_major": 2}, {"valid_until": iso(AT)}, {"published_at": iso(AT + timedelta(days=1))},
    {"targets": {"DEMOA": "0.8", "DEMOB": "0.8"}}, {"targets": {"FOREIGN": "0.5"}},
    {"targets": {"DEMOA": "NaN"}}, {"targets": {"DEMOA": 0.5}}, {"purpose": "live"},
    {"universe": ["DEMOA", "DEMOA"]}, {"run_command": "untrusted"},
])
def test_invalid_signed_payloads_refused(author, payload, change):
    trust, sign = author
    with pytest.raises(Refused):
        resolve_chain([sign({**payload, **change})], trust, AT)


def test_trust_is_scoped_to_package_and_purpose(author, payload):
    trust, sign = author
    wrong = deepcopy(trust)
    wrong["test-key"]["packages"] = ["different"]
    with pytest.raises(Refused, match="not trusted"):
        resolve_chain([sign(payload)], wrong, AT)
    trust["test-key"]["allow_paper"] = False
    with pytest.raises(Refused, match="demonstrations"):
        resolve_chain([sign(payload)], trust, AT)


def test_delta_install_and_wrong_base_are_atomic(store, author, payload):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    delta = delta_for(payload, edition_id="edition-2", published_at=iso(AT - timedelta(days=1)), research="Updated research")
    broken = {**delta, "base_sha256": "0" * 64}
    with pytest.raises(Refused, match="base"):
        store.install(sign(broken, "delta"), trust, AT)
    assert store.load_package(payload["package_id"], trust, AT)[0] == payload
    updated = store.install(sign(delta, "delta"), trust, AT)
    assert updated["research"] == "Updated research"
    assert store.load_package(payload["package_id"], trust, AT)[0] == updated
    with pytest.raises(Refused, match="downgrade"):
        store.install(sign(payload), trust, AT)


def test_delta_cannot_change_identity_or_lie_about_result(author, payload):
    trust, sign = author
    delta = delta_for(payload, edition_id="edition-2", published_at=iso(AT - timedelta(days=1)))
    delta["result_sha256"] = "0" * 64
    with pytest.raises(Refused, match="result hash"):
        resolve_chain([sign(payload), sign(delta, "delta")], trust, AT)
    delta = delta_for(payload, purpose="demo", edition_id="edition-2")
    with pytest.raises(Refused, match="replacements"):
        resolve_chain([sign(payload), sign(delta, "delta")], trust, AT)


def test_expired_base_can_receive_fresh_delta(store, author, payload):
    trust, sign = author
    payload["valid_until"] = iso(AT + timedelta(seconds=1))
    store.install(sign(payload), trust, AT)
    later = AT + timedelta(days=1)
    delta = delta_for(payload, edition_id="edition-2", published_at=iso(AT), valid_until=iso(later + timedelta(days=1)))
    updated = store.install(sign(delta, "delta"), trust, later)
    assert updated["edition_id"] == "edition-2"


def test_installed_provenance_is_reverified(store, author, payload):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    store.db.execute("UPDATE editions SET hash=?", ("0" * 64,))
    with pytest.raises(Refused, match="identity"):
        store.load_package(payload["package_id"], trust, AT)


def test_duplicate_keys_and_nonfinite_numbers_are_rejected():
    for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
        with pytest.raises(Refused):
            loads(raw)
