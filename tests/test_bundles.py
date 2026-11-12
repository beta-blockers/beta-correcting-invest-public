"""Signed release inventories: sign release and verify-bundle."""
import os
import re
from datetime import timedelta

import pytest

from conftest import AT
from public_pilot import authoring
from public_pilot.bundles import verify_bundle
from public_pilot.common import Refused
from support import call, freeze, new_key, read, trust_for, write

KEY_ID = "test-key"
LATER = AT + timedelta(days=60)


@pytest.fixture
def signer(tmp_path):
    directory = tmp_path / "keys"
    directory.mkdir(mode=0o700)
    private, created = new_key(directory)
    return private, created["key"]


@pytest.fixture
def trust(signer):
    return trust_for(signer[0], KEY_ID, "test-author", ["test-research"])


def make_bundle(root, private, payload, extra=()):
    """A fictional data bundle signed as a release; extra names are added before signing."""
    (root / "data").mkdir(parents=True)
    edition = authoring.sign_snapshot(private, KEY_ID, {**payload, "purpose": "demo"}, AT)
    authoring.write_new(root / "edition.snapshot.json", edition)
    (root / "REPORT.md").write_text("# Fictional report\n")
    write(root / "data" / "fixture.json", {"note": "fictional"})
    for name in extra:
        write(root / name, {})
    authoring.write_new(root / "release.json", authoring.sign_release(private, KEY_ID, root, "edition.snapshot.json", AT))
    return root


def resign(root, private, **changes):
    """Replace release.json with a validly signed release carrying the given changes."""
    body = {k: v for k, v in read(root / "release.json").items() if k != "signature"}
    body.update(changes)
    (root / "release.json").unlink()
    write(root / "release.json", authoring.sign(private, body))


def test_bundle_of_exactly_the_listed_files_passes(tmp_path, signer, trust, payload, monkeypatch, capsys):
    root = make_bundle(tmp_path / "bundle", signer[0], payload)
    release = read(root / "release.json")
    assert release["format"] == "public-pilot-release-v1" and release["snapshot"] == "edition.snapshot.json"
    assert sorted(release["files"]) == ["REPORT.md", "data/fixture.json", "edition.snapshot.json"]
    freeze(monkeypatch, AT)
    code, output = call(capsys, ["--trust", write(tmp_path / "trust.json", trust), "verify-bundle", root])
    assert code == 0 and output == {"status": "verified", "package_id": "test-research", "edition_id": "edition-1",
                                    "files_verified": 3, "expired": False}


def test_sign_release_command_writes_release_json(tmp_path, signer, trust, payload, monkeypatch, capsys):
    root = tmp_path / "bundle"
    root.mkdir()
    authoring.write_new(root / "edition.snapshot.json",
                        authoring.sign_snapshot(signer[0], KEY_ID, {**payload, "purpose": "demo"}, AT))
    freeze(monkeypatch, AT)
    code, output = call(capsys, ["sign", "release", root, "edition.snapshot.json", "--key", signer[1],
                                 "--key-id", KEY_ID])
    assert code == 0 and output["files"] == 1 and verify_bundle(root, trust, AT)["status"] == "verified"
    code, refusal = call(capsys, ["sign", "release", root, "edition.snapshot.json", "--key", signer[1],
                                  "--key-id", KEY_ID])
    assert code == 2 and "already exists" in refusal["reason"]


@pytest.mark.parametrize("damage, message", [
    ("changed", "Release file changed: REPORT.md"),
    ("missing", "Release file is missing: data/fixture.json"),
    ("extra", "Unlisted file in release: notes.txt"),
    ("nested-extra", "Unlisted file in release: data/extra.json"),
    ("cache", "Unlisted file in release: __pycache__/module.pyc"),
    ("hidden", "Unlisted file in release: .DS_Store"),
])
def test_changed_missing_and_extra_files_each_fail(tmp_path, signer, trust, payload, damage, message):
    root = make_bundle(tmp_path / "bundle", signer[0], payload)
    if damage == "changed":
        (root / "REPORT.md").write_text("# Altered after signing\n")
    elif damage == "missing":
        (root / "data" / "fixture.json").unlink()
    elif damage == "extra":
        (root / "notes.txt").write_text("stray")
    elif damage == "nested-extra":
        write(root / "data" / "extra.json", {})
    elif damage == "cache":
        (root / "__pycache__").mkdir()
        (root / "__pycache__" / "module.pyc").write_bytes(b"\0")
    else:
        (root / ".DS_Store").write_bytes(b"\0")
    with pytest.raises(Refused, match=re.escape(message)):
        verify_bundle(root, trust, AT)


def test_root_release_json_is_the_only_exempt_file(tmp_path, signer, trust, payload):
    root = make_bundle(tmp_path / "bundle", signer[0], payload, extra=["data/release.json"])
    assert "data/release.json" in read(root / "release.json")["files"]
    assert verify_bundle(root, trust, AT)["files_verified"] == 4
    (root / "data" / "release.json").unlink()
    with pytest.raises(Refused, match="missing: data/release.json"):
        verify_bundle(root, trust, AT)


def test_bundle_holding_an_expired_snapshot_passes_with_expired_true(tmp_path, signer, trust, payload,
                                                                     monkeypatch, capsys):
    root = make_bundle(tmp_path / "bundle", signer[0], payload)
    freeze(monkeypatch, LATER)
    code, output = call(capsys, ["--trust", write(tmp_path / "trust.json", trust), "verify-bundle", root])
    assert code == 0 and output["expired"] is True
    with pytest.raises(Refused, match="Future-dated research"):
        verify_bundle(root, trust, AT - timedelta(days=3))


@pytest.mark.parametrize("kind", ["file-link", "directory-link", "hard-link", "fifo"])
def test_links_and_special_files_are_refused_when_signing_and_verifying(tmp_path, signer, trust, payload, kind):
    root = make_bundle(tmp_path / "bundle", signer[0], payload)
    if kind == "file-link":
        (root / "link.md").symlink_to(root / "REPORT.md")
    elif kind == "directory-link":
        (root / "linked").symlink_to(root / "data", target_is_directory=True)
    elif kind == "hard-link":
        os.link(root / "REPORT.md", root / "copy.md")
    else:
        os.mkfifo(root / "pipe")
    with pytest.raises(Refused, match="Linked|Hard-linked|Special"):
        verify_bundle(root, trust, AT)
    (root / "release.json").unlink()
    with pytest.raises(Refused, match="Linked|Hard-linked|Special"):
        authoring.sign_release(signer[0], KEY_ID, root, "edition.snapshot.json", AT)


@pytest.mark.parametrize("name", ["/etc/hosts", "../outside.json", "data/../REPORT.md", "./REPORT.md",
                                  "data//fixture.json", "back\\slash.json", "release.json"])
def test_listed_paths_must_stay_inside_the_bundle(tmp_path, signer, trust, payload, name):
    root = make_bundle(tmp_path / "bundle", signer[0], payload)
    files = {**read(root / "release.json")["files"], name: "0" * 64}
    resign(root, signer[0], files=files)
    with pytest.raises(Refused, match="Release path refused|cannot list itself"):
        verify_bundle(root, trust, AT)


def test_release_signature_and_trust_scope_are_enforced(tmp_path, signer, trust, payload):
    private, _ = signer
    root = make_bundle(tmp_path / "bundle", private, payload)
    original = (root / "release.json").read_text()
    release = read(root / "release.json")
    (root / "release.json").unlink()
    write(root / "release.json", {**release, "files": {**release["files"], "REPORT.md": "0" * 64}})
    with pytest.raises(Refused, match="signature"):
        verify_bundle(root, trust, AT)
    (root / "release.json").unlink()
    (root / "release.json").write_text(original)
    with pytest.raises(Refused, match="not in the local trust store"):
        verify_bundle(root, {}, AT)
    with pytest.raises(Refused, match="not trusted for this package"):
        verify_bundle(root, trust_for(private, KEY_ID, "test-author", ["another-package"]), AT)
    resign(root, private, package_id="another-package")
    both = trust_for(private, KEY_ID, "test-author", ["test-research", "another-package"])
    with pytest.raises(Refused, match="package identity mismatch"):
        verify_bundle(root, both, AT)


def test_release_signed_by_another_authors_key_is_refused(tmp_path, signer, trust, payload):
    root = make_bundle(tmp_path / "bundle", signer[0], payload)
    other, _ = new_key(tmp_path / "keys", "other.key")
    body = {k: v for k, v in read(root / "release.json").items() if k != "signature"}
    (root / "release.json").unlink()
    write(root / "release.json", authoring.sign(other, {**body, "key_id": "other-key"}))
    combined = {**trust, **trust_for(other, "other-key", "other-author", ["test-research"])}
    with pytest.raises(Refused, match="Release author mismatch"):
        verify_bundle(root, combined, AT)


def test_signer_refuses_missing_snapshots_and_other_keys(tmp_path, signer, payload):
    root = make_bundle(tmp_path / "bundle", signer[0], payload)
    (root / "release.json").unlink()
    with pytest.raises(Refused, match="outside the release inventory"):
        authoring.sign_release(signer[0], KEY_ID, root, "absent.json", AT)
    other, _ = new_key(tmp_path / "keys", "other.key")
    with pytest.raises(Refused, match="signature"):
        authoring.sign_release(other, KEY_ID, root, "edition.snapshot.json", AT)
    with pytest.raises(Refused, match="no release.json"):
        verify_bundle(root, {}, AT)


def test_a_fifo_release_json_is_refused_without_blocking(tmp_path, signer, trust, payload):
    import json
    import subprocess
    import sys
    root = make_bundle(tmp_path / "bundle", signer[0], payload)
    (root / "release.json").unlink()
    os.mkfifo(root / "release.json")
    trust_file = write(tmp_path / "trust.json", trust)
    source = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run([sys.executable, "-m", "public_pilot", "--trust", trust_file, "verify-bundle", str(root)],
                            capture_output=True, text=True, timeout=30, env={**os.environ, "PYTHONPATH": source})
    assert result.returncode == 2 and "special file refused" in json.loads(result.stderr)["reason"]
