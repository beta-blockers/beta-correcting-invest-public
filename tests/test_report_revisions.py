"""An exact editorial transition cannot authorize a research edit or judge its own PR."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from public_pilot import authoring, catalog, report_revisions
from public_pilot.bundles import file_sha256
from public_pilot.common import Refused
from support import NOW, build_repository, read, write

ROOT = Path(__file__).resolve().parents[1]
EDITION = "history/demo-product/2020-Q1"


def hashes(directory):
    return {name: file_sha256(directory / name) for name in catalog.EDITION_FILES}


@pytest.fixture
def revision(tmp_path, monkeypatch):
    private = Ed25519PrivateKey.generate()
    tree = build_repository(tmp_path / "candidate", private)
    base = tmp_path / "base"
    shutil.copytree(tree, base)
    report = tree / EDITION / "REPORT.md"
    report.write_text("# A clearer explanation of the same research\n\n" + report.read_text())
    release = tree / EDITION / "release.json"
    release.unlink()
    authoring.write_new(release, authoring.sign_release(private, "demo-key", release.parent,
                                                       "edition.snapshot.json", NOW))
    permission = (hashes(base / EDITION), hashes(tree / EDITION))
    monkeypatch.setattr(report_revisions, "REPORT_REVISIONS", {EDITION: permission})
    return base, tree, private, permission


def test_approved_report_revision_passes_signatures_binding_and_base_comparison(revision):
    base, tree, _, _ = revision
    assert catalog.check(tree, NOW, base)["append_only"] is True
    # The ordinary unchanged-base case remains valid after the editorial update.
    assert catalog.check(tree, NOW, tree)["append_only"] is True


@pytest.mark.parametrize("side", ["base", "candidate"])
@pytest.mark.parametrize("name", catalog.EDITION_FILES)
def test_every_approved_file_is_pinned_on_both_sides(revision, side, name):
    base, tree, _, _ = revision
    path = (base if side == "base" else tree) / EDITION / name
    path.write_bytes(path.read_bytes() + b"\n")
    assert not report_revisions.matches_report_revision(EDITION, base / EDITION, tree / EDITION)


@pytest.mark.parametrize("damage", ["report", "scores", "weights", "fixture"])
def test_even_a_new_valid_signature_cannot_expand_the_approval(revision, damage):
    base, tree, private, _ = revision
    directory = tree / EDITION
    if damage == "report":
        report = directory / "REPORT.md"
        report.write_text("An unapproved further edit.\n" + report.read_text())
    elif damage == "scores":
        evaluation = read(directory / "evaluation.json")
        evaluation["payload"]["companies"]["DEMOA"]["composite"] = "73"
        write(directory / "evaluation.json", authoring.sign_evaluation(
            private, "demo-key", evaluation["payload"], read(directory / "edition.snapshot.json"), NOW))
    elif damage == "weights":
        snapshot = read(directory / "edition.snapshot.json")
        snapshot["payload"]["targets"]["DEMOA"] = "0.44"
        write(directory / "edition.snapshot.json", authoring.envelope(private, "demo-key", snapshot["payload"]))
    else:
        fixture = read(directory / "account.fixture.json")
        fixture["cash"] = "900"
        write(directory / "account.fixture.json", fixture)
    (directory / "release.json").unlink()
    authoring.write_new(directory / "release.json", authoring.sign_release(
        private, "demo-key", directory, "edition.snapshot.json", NOW))
    # Directly exercise the history guard as well as the full signature path above.
    with pytest.raises(Refused, match="history/ is append-only"):
        catalog.check_against_base(base, tree)


def test_permission_is_directional_and_specific_to_its_edition(revision):
    base, tree, _, _ = revision
    with pytest.raises(Refused, match="history/ is append-only"):
        catalog.check_against_base(tree, base)
    assert not report_revisions.matches_report_revision("history/other-product/2020-Q1",
                                                        base / EDITION, tree / EDITION)


def test_signature_still_required_even_when_history_hashes_match(revision, monkeypatch):
    base, tree, _, _ = revision
    release = tree / EDITION / "release.json"
    document = read(release)
    document["signature"] = "A" * 86 + "=="
    write(release, document)
    monkeypatch.setattr(report_revisions, "REPORT_REVISIONS",
                        {EDITION: (hashes(base / EDITION), hashes(tree / EDITION))})
    assert report_revisions.matches_report_revision(EDITION, base / EDITION, tree / EDITION)
    with pytest.raises(Refused, match="signature"):
        catalog.check(tree, NOW, base)


@pytest.mark.parametrize("approved", [False, True])
def test_candidate_cannot_supply_its_own_permission(revision, tmp_path, approved):
    base, tree, _, permission = revision
    shutil.copytree(ROOT / "src", base / "src", ignore=shutil.ignore_patterns("__pycache__"))
    trusted = base / "src/public_pilot/report_revisions.py"
    if approved:
        trusted.write_text(trusted.read_text() + f"\nREPORT_REVISIONS = {{{EDITION!r}: {permission!r}}}\n")
    planted = tree / "src/public_pilot/report_revisions.py"
    planted.parent.mkdir(parents=True)
    marker = tmp_path / "candidate-code-ran"
    planted.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
                       "def matches_report_revision(*args):\n    return True\n")
    script = """import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / 'src'))
from public_pilot.catalog import check
from public_pilot.common import now
check(Path(sys.argv[2]), now(), Path(sys.argv[1]))
"""
    result = subprocess.run([sys.executable, "-I", "-c", script, str(base), str(tree)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=30)
    assert not marker.exists(), result.stderr
    assert (result.returncode == 0) == approved, result.stderr
    if not approved:
        assert "history/ is append-only" in result.stderr


def test_real_permission_pins_five_files_and_preserves_all_research():
    assert set(report_revisions.REPORT_REVISIONS) == {"history/usmaterials/2026-Q4"}
    before, after = report_revisions.REPORT_REVISIONS["history/usmaterials/2026-Q4"]
    assert set(before) == set(after) == set(catalog.EDITION_FILES)
    assert {name for name in before if before[name] != after[name]} == {"REPORT.md", "release.json"}
    assert all(len(value) == 64 and int(value, 16) >= 0 for side in (before, after) for value in side.values())
