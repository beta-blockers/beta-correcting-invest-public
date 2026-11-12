"""Author tools: keygen, fingerprint, validate and sign. Keys are generated per test."""
import base64
import hashlib
import os
from datetime import timedelta
from pathlib import Path

import pytest

from conftest import AT
from public_pilot import authoring
from public_pilot.common import Refused, digest, iso
from public_pilot.packages import resolve_chain
from support import call, freeze, new_key, read, trust_for, write

KEY_ID = "test-key"
LATER = AT + timedelta(days=60)


@pytest.fixture
def keys(tmp_path):
    directory = tmp_path / "keys"
    directory.mkdir(mode=0o700)
    return directory


@pytest.fixture
def signer(keys):
    private, created = new_key(keys)
    return private, created["key"]


# keygen and fingerprint ---------------------------------------------------------

def test_keygen_writes_an_owner_only_raw_key_and_prints_its_fingerprint(keys, capsys):
    path = keys / "author.key"
    code, output = call(capsys, ["keygen", "--out", path])
    assert code == 0 and set(output) == {"status", "key", "public_key", "fingerprint_sha256"}
    assert path.stat().st_mode & 0o777 == 0o600 and path.stat().st_size == 32
    assert output["public_key"] == authoring.public_key(authoring.load_private_key(path))
    assert output["fingerprint_sha256"] == hashlib.sha256(base64.b64decode(output["public_key"])).hexdigest()


def test_keygen_never_overwrites_a_file_or_follows_a_link(keys, capsys):
    path = keys / "author.key"
    path.write_bytes(b"existing")
    code, refusal = call(capsys, ["keygen", "--out", path])
    assert code == 2 and "never overwrites" in refusal["reason"]
    assert path.read_bytes() == b"existing"
    (keys / "link.key").symlink_to(keys / "target.key")
    assert call(capsys, ["keygen", "--out", keys / "link.key"])[0] == 2
    assert not (keys / "target.key").exists()


@pytest.mark.parametrize("marker", ["directory", "worktree-file"])
def test_keygen_refuses_a_path_inside_a_git_checkout(tmp_path, capsys, marker):
    checkout = tmp_path / "checkout"
    (checkout / "nested").mkdir(parents=True)
    if marker == "directory":
        (checkout / ".git").mkdir()
    else:
        (checkout / ".git").write_text("gitdir: /elsewhere/.git/worktrees/checkout\n")
    code, refusal = call(capsys, ["keygen", "--out", checkout / "nested" / "author.key"])
    assert code == 2 and "outside every Git checkout" in refusal["reason"]
    assert not (checkout / "nested" / "author.key").exists()


def test_fingerprint_is_sha256_of_the_raw_public_key(signer, capsys):
    public = authoring.public_key(signer[0])
    code, output = call(capsys, ["fingerprint", public])
    assert code == 0 and output["fingerprint_sha256"] == hashlib.sha256(base64.b64decode(public)).hexdigest()
    for bad in ("not base64!", base64.b64encode(b"short").decode(), public[:-4]):
        assert call(capsys, ["fingerprint", bad])[0] == 2


# validate -------------------------------------------------------------------------

def test_validate_reports_the_first_failure(tmp_path, payload, monkeypatch, capsys):
    path = write(tmp_path / "payload.json", payload)
    code, output = call(capsys, ["validate", path, "--as-of", iso(AT)])
    assert code == 0 and output == {"status": "valid", "package_id": "test-research",
                                    "edition_id": "edition-1", "sha256": digest(payload)}
    broken = write(tmp_path / "broken.json", {**payload, "engine_major": 2, "targets": {"DEMOA": "2"}})
    code, refusal = call(capsys, ["validate", broken, "--as-of", iso(AT)])
    assert code == 2 and refusal == {"status": "refused", "reason": "Unsupported engine compatibility"}
    code, refusal = call(capsys, ["validate", path, "--as-of", iso(LATER)])
    assert code == 2 and refusal["reason"] == "Expired or future-dated research"
    freeze(monkeypatch, AT)
    assert call(capsys, ["validate", path])[0] == 0


def shared_fixtures(payload):
    before_cutoff = iso(AT - timedelta(days=4))
    evidence = {"title": "Fictional notice", "url": "https://example.com/notice", "published_at": before_cutoff}
    valid = {
        "minimal": payload,
        "demo": {**payload, "purpose": "demo"},
        "exit-and-cash": {**payload, "universe": ["DEMOA", "DEMOB", "DEMOC"], "targets": {"DEMOA": "0.5", "DEMOC": "0"}},
        "integer-weight": {**payload, "targets": {"DEMOA": 1}},
        "evidence": {**payload, "evidence": [evidence]},
    }
    invalid = {
        "unknown-field": {**payload, "run_command": "untrusted"},
        "missing-field": {k: v for k, v in payload.items() if k != "research"},
        "engine-major": {**payload, "engine_major": 2},
        "live-purpose": {**payload, "purpose": "live"},
        "bad-edition-id": {**payload, "edition_id": "bad id"},
        "expired": {**payload, "valid_until": iso(AT)},
        "future": {**payload, "published_at": iso(AT + timedelta(days=1))},
        "cutoff-after-publication": {**payload, "information_cutoff": iso(AT - timedelta(days=1))},
        "overweight": {**payload, "targets": {"DEMOA": "0.6", "DEMOB": "0.6"}},
        "foreign-target": {**payload, "targets": {"OTHER": "0.1"}},
        "nan-weight": {**payload, "targets": {"DEMOA": "NaN"}},
        "float-weight": {**payload, "targets": {"DEMOA": 0.5}},
        "duplicate-universe": {**payload, "universe": ["DEMOA", "DEMOA"]},
        "lowercase-symbol": {**payload, "universe": ["demoa"], "targets": {"demoa": "0.1"}},
        "http-evidence": {**payload, "evidence": [{**evidence, "url": "http://example.com/notice"}]},
        "late-evidence": {**payload, "evidence": [{**evidence, "published_at": iso(AT - timedelta(days=1))}]},
        "evidence-extra-field": {**payload, "evidence": [{**evidence, "fetch": True}]},
        "empty-geographies": {**payload, "geographies": []},
        "naive-timestamp": {**payload, "published_at": "2029-12-31T15:00:00"},
        "research-not-text": {**payload, "research": ["text"]},
        "not-an-object": ["not", "a", "payload"],
    }
    return valid, invalid


def test_validate_and_install_agree_on_shared_fixtures(tmp_path, author, payload, monkeypatch, capsys):
    trust, sign = author
    freeze(monkeypatch, AT)
    trust_file = write(tmp_path / "trust.json", trust)
    valid, invalid = shared_fixtures(payload)
    for expected, fixtures in ((0, valid), (2, invalid)):
        for name, document in fixtures.items():
            validated, _ = call(capsys, ["validate", write(tmp_path / f"{name}.json", document), "--as-of", iso(AT)])
            installed, _ = call(capsys, ["--state", tmp_path / f"state-{name}", "--trust", trust_file, "install",
                                         write(tmp_path / f"{name}.signed.json", sign(document))])
            assert validated == installed == expected, name


# sign ---------------------------------------------------------------------------

def test_signed_snapshot_and_delta_install_with_the_existing_install(tmp_path, signer, payload, monkeypatch, capsys):
    private, key = signer
    freeze(monkeypatch, AT)
    trust = write(tmp_path / "trust.json", trust_for(private, KEY_ID, "test-author", ["test-research"], True))
    newer = {**payload, "edition_id": "edition-2", "published_at": iso(AT - timedelta(days=1)),
             "targets": {"DEMOA": "0.5", "DEMOB": "0.3"}}
    base, new = write(tmp_path / "base.json", payload), write(tmp_path / "new.json", newer)
    key_args = ["--key", key, "--key-id", KEY_ID]
    code, signed = call(capsys, ["sign", "snapshot", base, tmp_path / "base.snapshot.json"] + key_args)
    assert code == 0 and signed["sha256"] == digest(payload)
    assert call(capsys, ["sign", "snapshot", new, tmp_path / "new.snapshot.json"] + key_args)[0] == 0
    code, signed = call(capsys, ["sign", "delta", base, new, tmp_path / "new.delta.json"] + key_args)
    assert code == 0 and signed["sha256"] == digest(newer)
    assert read(tmp_path / "new.delta.json")["payload"]["replace"] == {
        "edition_id": "edition-2", "published_at": newer["published_at"], "targets": newer["targets"]}
    state = ["--state", tmp_path / "state", "--trust", trust]
    code, installed = call(capsys, state + ["install", tmp_path / "base.snapshot.json"])
    assert code == 0 and installed["sha256"] == digest(payload)
    code, updated = call(capsys, state + ["install", tmp_path / "new.delta.json"])
    assert code == 0 and updated["edition_id"] == "edition-2" and updated["sha256"] == digest(newer)
    fresh = ["--state", tmp_path / "fresh", "--trust", trust]
    assert call(capsys, fresh + ["install", tmp_path / "new.snapshot.json"])[1]["sha256"] == updated["sha256"]


def test_delta_chain_and_full_snapshot_resolve_to_the_same_payload(signer, payload):
    private, _ = signer
    trust = trust_for(private, KEY_ID, "test-author", ["test-research"], True)
    updated = {**payload, "edition_id": "edition-2", "published_at": iso(AT - timedelta(days=1)),
               "research": "Fictional next edition."}
    chain = [authoring.sign_snapshot(private, KEY_ID, payload, AT),
             authoring.sign_delta(private, KEY_ID, payload, updated, AT)]
    full = [authoring.sign_snapshot(private, KEY_ID, updated, AT)]
    assert resolve_chain(chain, trust, AT) == resolve_chain(full, trust, AT) == updated


def test_signing_self_checks_and_writes_nothing_on_failure(tmp_path, signer, payload, monkeypatch, capsys):
    _, key = signer
    freeze(monkeypatch, AT)
    out = tmp_path / "out.json"
    key_args = ["--key", key, "--key-id", KEY_ID]
    for broken in ({**payload, "targets": {"DEMOA": "0.9", "DEMOB": "0.9"}}, {**payload, "valid_until": iso(AT)}):
        assert call(capsys, ["sign", "snapshot", write(tmp_path / "bad.json", broken), out] + key_args)[0] == 2
        assert not out.exists()
    base = write(tmp_path / "base.json", payload)
    demo = {**payload, "edition_id": "edition-2", "published_at": iso(AT - timedelta(days=1)), "purpose": "demo"}
    code, refusal = call(capsys, ["sign", "delta", base, write(tmp_path / "demo.json", demo), out] + key_args)
    assert code == 2 and "replacements" in refusal["reason"]
    stale = {**payload, "edition_id": "edition-2", "research": "Same publication time."}
    code, refusal = call(capsys, ["sign", "delta", base, write(tmp_path / "stale.json", stale), out] + key_args)
    assert code == 2 and "advance" in refusal["reason"] and not out.exists()
    code, refusal = call(capsys, ["sign", "snapshot", base, out, "--key", key, "--key-id", "bad key id"])
    assert code == 2 and "Key IDs" in refusal["reason"] and not out.exists()


def test_signed_documents_are_never_overwritten(tmp_path, signer, payload, monkeypatch, capsys):
    freeze(monkeypatch, AT)
    out = tmp_path / "edition.json"
    out.write_text("{}")
    code, refusal = call(capsys, ["sign", "snapshot", write(tmp_path / "payload.json", payload), out,
                                  "--key", signer[1], "--key-id", KEY_ID])
    assert code == 2 and "never overwritten" in refusal["reason"] and out.read_text() == "{}"


def test_as_of_signs_an_already_expired_demo_edition_only(tmp_path, signer, payload, monkeypatch, capsys):
    private, key = signer
    freeze(monkeypatch, LATER)
    key_args = ["--key", key, "--key-id", KEY_ID]
    demo = write(tmp_path / "demo.json", {**payload, "purpose": "demo"})
    code, refusal = call(capsys, ["sign", "snapshot", demo, tmp_path / "a.json"] + key_args)
    assert code == 2 and refusal["reason"] == "Expired or future-dated research"
    assert call(capsys, ["sign", "snapshot", demo, tmp_path / "a.json", "--as-of", iso(AT)] + key_args)[0] == 0
    paper = write(tmp_path / "paper.json", payload)
    code, refusal = call(capsys, ["sign", "snapshot", paper, tmp_path / "b.json", "--as-of", iso(AT)] + key_args)
    assert code == 2 and "purpose demo" in refusal["reason"] and not (tmp_path / "b.json").exists()
    newer = write(tmp_path / "newer.json", {**payload, "purpose": "demo", "edition_id": "edition-2",
                                            "published_at": iso(AT - timedelta(days=1))})
    assert call(capsys, ["sign", "delta", demo, newer, tmp_path / "d.json", "--as-of", iso(AT)] + key_args)[0] == 0
    trust = write(tmp_path / "trust.json", trust_for(private, KEY_ID, "test-author", ["test-research"]))
    state = ["--state", tmp_path / "state", "--trust", trust]
    assert call(capsys, state + ["install", tmp_path / "a.json"])[0] == 2
    code, installed = call(capsys, state + ["install", tmp_path / "a.json", "--allow-expired"])
    assert code == 0 and installed["expired"] is True
    code, updated = call(capsys, state + ["install", tmp_path / "d.json", "--allow-expired"])
    assert code == 0 and updated["edition_id"] == "edition-2" and updated["expired"] is True
    # A future --as-of is refused even when the edition would be valid at that instant.
    freeze(monkeypatch, AT)
    code, refusal = call(capsys, ["sign", "snapshot", demo, tmp_path / "c.json",
                                  "--as-of", iso(AT + timedelta(days=1))] + key_args)
    assert code == 2 and refusal["reason"] == "--as-of cannot be in the future"
    assert not (tmp_path / "c.json").exists()


def test_signing_keys_must_be_private_unlinked_files_outside_checkouts(tmp_path, keys, signer, payload,
                                                                       monkeypatch, capsys):
    _, key = signer
    freeze(monkeypatch, AT)
    source = write(tmp_path / "payload.json", payload)

    def sign_with(path):
        return call(capsys, ["sign", "snapshot", source, tmp_path / "out.json", "--key", path, "--key-id", KEY_ID])

    raw = Path(key).read_bytes()
    loose = keys / "loose.key"
    loose.write_bytes(raw)
    loose.chmod(0o640)
    assert "owner-only" in sign_with(loose)[1]["reason"]
    (keys / "link.key").symlink_to(key)
    assert "not a link" in sign_with(keys / "link.key")[1]["reason"]
    os.link(key, keys / "hard.key")
    assert "hard-linked" in sign_with(keys / "hard.key")[1]["reason"]
    assert "hard-linked" in sign_with(key)[1]["reason"]
    os.unlink(keys / "hard.key")
    short = keys / "short.key"
    short.write_bytes(raw[:31])
    short.chmod(0o600)
    assert "32-byte" in sign_with(short)[1]["reason"]
    checkout = tmp_path / "checkout"
    (checkout / ".git").mkdir(parents=True)
    inside = checkout / "author.key"
    inside.write_bytes(raw)
    inside.chmod(0o600)
    assert "outside every Git checkout" in sign_with(inside)[1]["reason"]
    assert not (tmp_path / "out.json").exists()
    assert sign_with(key)[0] == 0


def test_library_signing_rejects_non_object_payloads(signer):
    with pytest.raises(Refused, match="payload object"):
        authoring.sign_snapshot(signer[0], KEY_ID, ["not", "a", "payload"], AT)


def test_symbolic_link_loops_are_refused_not_crashing(keys, payload, tmp_path, monkeypatch, capsys):
    freeze(monkeypatch, AT)
    loop = keys / "loop.key"
    loop.symlink_to(loop)
    code, refusal = call(capsys, ["sign", "snapshot", write(tmp_path / "payload.json", payload), tmp_path / "out.json",
                                  "--key", loop, "--key-id", KEY_ID])
    assert code == 2 and refusal["status"] == "refused"
    code, refusal = call(capsys, ["keygen", "--out", loop / "author.key"])
    assert code == 2 and refusal["status"] == "refused"


def test_out_of_range_timestamps_are_refused_not_crashing(tmp_path, payload, capsys):
    path = write(tmp_path / "payload.json", payload)
    code, refusal = call(capsys, ["validate", path, "--as-of", "0001-01-01T00:00:00+05:00"])
    assert code == 2 and refusal["reason"] == "Date or time out of range"
    early = write(tmp_path / "early.json", {**payload, "information_cutoff": "0001-01-01T00:00:00+05:00"})
    code, refusal = call(capsys, ["validate", early, "--as-of", iso(AT)])
    assert code == 2 and refusal["reason"] == "Date or time out of range"
