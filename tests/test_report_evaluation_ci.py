"""Changed editions use the trusted renderer; old reports and PR code cannot affect the check."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from public_pilot import authoring, catalog
from public_pilot.bundles import verify_bundle
from public_pilot.evaluation import verify_evaluation
from support import (NOW, SIGNED_AT, build_repository, edition_payload, evaluation_payload, read,
                     trust_for, write, write_edition)
from test_workflow import COMMON_STUB, git, step_script

ROOT = Path(__file__).resolve().parents[1]
STEP = "Catalog and history pass the base branch's checks"
CHECKER = "scripts/check_report_evaluation.py"
EDITION = Path("history/demo-product/2020-Q1")
pytestmark = pytest.mark.skipif(shutil.which("bash") is None or shutil.which("git") is None,
                                reason="needs bash and git")


def trusted_base(path):
    shutil.copytree(ROOT / "src", path / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (path / "scripts").mkdir()
    shutil.copyfile(ROOT / CHECKER, path / CHECKER)
    return path


@pytest.fixture
def sample(tmp_path):
    private = Ed25519PrivateKey.generate()
    repo = build_repository(tmp_path / "checkout", private)
    base = trusted_base(tmp_path / "base")
    return repo, base, private


def run_check(repo, base, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir(exist_ok=True)
    return subprocess.run([sys.executable, "-I", str(base / CHECKER), str(base), str(repo)],
                          cwd=outside, capture_output=True, text=True, timeout=30)


def change_renderer(base):
    source = base / "src/public_pilot/evaluation.py"
    # Do not freeze a particular sentence in the regression test itself: any renderer wording may evolve.
    source.write_text(source.read_text() + '\n\n_original_render = render\n'
                      'def render(document):\n'
                      '    return _original_render(document) + "\\nChanged standard wording.\\n"\n')


def test_published_reports_do_not_freeze_renderer_wording_and_are_never_modified(tmp_path):
    repo = tmp_path / "checkout"
    base = trusted_base(tmp_path / "base")
    shutil.copytree(ROOT / "history", repo / "history")
    shutil.copytree(ROOT / "history", base / "history")
    before = {p.relative_to(repo): p.read_bytes() for p in (repo / "history").rglob("*") if p.is_file()}
    change_renderer(base)
    result = run_check(repo, base, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "published reports were not re-rendered" in result.stdout
    assert "matches render-evaluation exactly" not in result.stdout
    assert {p.relative_to(repo): p.read_bytes() for p in (repo / "history").rglob("*") if p.is_file()} == before


def test_new_edition_accepts_narrative_before_the_complete_rendered_section(sample, tmp_path):
    repo, base, _ = sample
    report = repo / EDITION / "REPORT.md"
    report.write_text("# Fictional research narrative\n\n" + report.read_text())
    result = run_check(repo, base, tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("matches render-evaluation exactly") == 1


def test_re_signed_stale_hash_is_refused_even_though_signature_checks_pass(sample, tmp_path):
    repo, base, private = sample
    edition = repo / EDITION
    evaluation = read(edition / "evaluation.json")
    report = edition / "REPORT.md"
    report.write_text(report.read_text().replace(evaluation["payload"]["package_sha256"], "0" * 64))
    (edition / "release.json").unlink()
    authoring.write_new(edition / "release.json", authoring.sign_release(
        private, "demo-key", edition, "edition.snapshot.json", SIGNED_AT))
    trust = trust_for(private, "demo-key", "demo-author", ["demo-product"])
    verify_bundle(edition, trust, SIGNED_AT)
    verify_evaluation(evaluation, read(edition / "edition.snapshot.json"), trust, SIGNED_AT)
    result = run_check(repo, base, tmp_path)
    assert result.returncode != 0
    assert "history/demo-product/2020-Q1/REPORT.md: signed-evaluation section differs" in result.stderr
    assert "Published reports must remain unchanged" in result.stderr


@pytest.mark.parametrize("change", ["score", "missing", "duplicate", "wrong-edition", "truncated", "trailing-text"])
def test_changed_or_ambiguous_sections_are_refused(sample, tmp_path, change):
    repo, base, _ = sample
    shutil.copytree(repo / "history", base / "history")
    report = repo / EDITION / "REPORT.md"
    text = report.read_text()
    if change == "score":
        changed = text.replace("| 1 | DEMOA | 72 |", "| 1 | DEMOA | 73 |", 1)
    elif change == "missing":
        changed = "# Fictional research without an evaluation\n"
    elif change == "duplicate":
        changed = text + text
    elif change == "wrong-edition":
        changed = text.replace("edition demo-product-2020-q1", "edition demo-product-2020-q1-old", 1)
    elif change == "truncated":
        changed = text[:text.index("## Companies")]
    else:
        changed = text + "\nUnrendered trailing text.\n"
    assert changed != text
    report.write_text(changed)
    result = run_check(repo, base, tmp_path)
    assert result.returncode != 0
    assert "REPORT.md:" in result.stderr


@pytest.mark.parametrize("failure", ["missing", "malformed"])
def test_render_failure_stops_the_check(sample, tmp_path, failure):
    repo, base, _ = sample
    evaluation = repo / EDITION / "evaluation.json"
    if failure == "missing":
        evaluation.unlink()
    else:
        evaluation.write_text("not JSON\n")
    result = run_check(repo, base, tmp_path)
    assert result.returncode != 0
    assert "render-evaluation failed" in result.stderr
    assert "matches render-evaluation exactly" not in result.stdout


@pytest.mark.parametrize("stale", [False, True])
def test_only_the_added_edition_uses_the_new_base_renderer(sample, tmp_path, stale):
    repo, base, private = sample
    shutil.copytree(repo / "history", base / "history")
    change_renderer(base)
    payload = edition_payload(product="demo-other")
    added = write_edition(repo / "history/demo-other/2020-Q1", private, "demo-key", payload, evaluation_payload(payload))
    if not stale:
        report = added / "REPORT.md"
        report.write_text(report.read_text() + "\nChanged standard wording.\n")
    result = run_check(repo, base, tmp_path)
    assert (result.returncode != 0) == stale, result.stderr
    assert "history/demo-product/2020-Q1/REPORT.md" not in result.stdout + result.stderr
    assert "history/demo-other/2020-Q1/REPORT.md" in result.stdout + result.stderr


@pytest.mark.parametrize("file", ["edition.snapshot.json", "account.fixture.json", "evaluation.json"])
def test_selection_notices_content_changes_beyond_report_bytes(sample, tmp_path, file):
    repo, base, _ = sample
    shutil.copytree(repo / "history", base / "history")
    path = repo / EDITION / file
    data = read(path)
    if file == "edition.snapshot.json":
        data["payload"]["research"] = "Changed fictional research."
    elif file == "account.fixture.json":
        data["cash"] = "900"
    else:
        data["payload"]["method"]["description"] = "Changed fictional method."
    write(path, data)
    result = run_check(repo, base, tmp_path)
    if file == "evaluation.json":
        assert result.returncode != 0 and "signed-evaluation section differs" in result.stderr
    else:
        assert result.returncode == 0 and result.stdout.count("matches render-evaluation exactly") == 1


def test_signature_only_rotation_does_not_rerender_an_old_report(sample, tmp_path):
    repo, base, _ = sample
    shutil.copytree(repo / "history", base / "history")
    change_renderer(base)
    rotated = tmp_path / "rotated"
    catalog.resign_edition(repo / EDITION, rotated, Ed25519PrivateKey.generate(), "demo-next-key", NOW)
    shutil.rmtree(repo / EDITION)
    shutil.move(rotated, repo / EDITION)
    assert (repo / EDITION / "evaluation.json").read_bytes() != (base / EDITION / "evaluation.json").read_bytes()
    result = run_check(repo, base, tmp_path)
    assert result.returncode == 0 and "published reports were not re-rendered" in result.stdout


def test_no_history_change_is_a_successful_noop_and_a_missing_base_is_not(sample, tmp_path):
    repo, base, _ = sample
    shutil.rmtree(repo / "history")
    result = run_check(repo, base, tmp_path)
    assert result.returncode == 0 and "No added or content-changed editions" in result.stdout
    result = subprocess.run([sys.executable, "-I", str(base / CHECKER), str(base / "missing"), str(repo)],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0 and "existing directories" in result.stderr


# Exercise the actual base-rules step and clean-room blocks offline. Only the engine is stubbed here:
# the production checker, source selection, interpreter isolation and import attacks are real.
EXPECTED = "# Evaluation of demo-product, edition demo-product-2020-q1\n\nTrusted renderer.\n"
CATALOG_STUB = '''from pathlib import Path


def check(tree, now, base):
    return {"editions": []}


def history_editions(root):
    return [(p.parent.name, p.name, p) for p in sorted((Path(root) / "history").glob("*/*")) if p.is_dir()]


def edition_content(directory, where):
    return {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
'''


def commit(repo, message):
    git(repo, "add", "-A")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def workflow_repo(tmp_path, stale=False, bootstrap=False, behind=False):
    repo = tmp_path / "source"
    (repo / "src/public_pilot").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "catalog").mkdir()
    (repo / "catalog/authors.json").write_text("{}\n")
    (repo / "requirements.lock").write_text("# No dependencies for the offline test engine.\n")
    (repo / "src/public_pilot/__init__.py").write_text("")
    (repo / "src/public_pilot/common.py").write_text(COMMON_STUB)
    (repo / "src/public_pilot/catalog.py").write_text(CATALOG_STUB)
    (repo / "src/public_pilot/cli.py").write_text(
        f'def main(args):\n    assert args[0] == "render-evaluation"\n    print({EXPECTED!r}, end="")\n    return 0\n')
    git(repo, "init", "-q")
    if not bootstrap and not behind:
        shutil.copyfile(ROOT / CHECKER, repo / CHECKER)
    ancestor = commit(repo, "Base")
    if behind:
        shutil.copyfile(ROOT / CHECKER, repo / CHECKER)
        commit(repo, "Add trusted report rule to base")
    git(repo, "update-ref", "refs/remotes/origin/base", "HEAD")
    git(repo, "branch", "main", "HEAD")
    if behind:
        git(repo, "checkout", "-q", "--detach", ancestor)
    (repo / EDITION).mkdir(parents=True)
    (repo / EDITION / "REPORT.md").write_text(EXPECTED.replace("Trusted", "Stale") if stale else EXPECTED)
    (repo / EDITION / "evaluation.json").write_text("{}\n")
    marker = tmp_path / "untrusted-code-ran"
    planted = f'open({str(marker)!r}, "a").write(__file__)\nraise RuntimeError("Untrusted PR code ran")\n'
    for path in ("re.py", "scripts/re.py", "venv.py", "pip.py", "src/public_pilot/catalog.py", "src/public_pilot/cli.py"):
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(planted)
    # A permissive replacement is also ignored: only the base checker can judge this PR.
    (repo / CHECKER).write_text('def main(argv=None):\n    print("PR checker accepted everything")\n    return 0\n')
    commit(repo, "Proposed report and untrusted replacements")
    git(repo, "branch", "candidate", "HEAD")
    return repo, marker


def isolated_env(tmp_path, repo):
    bins = tmp_path / "bin"
    bins.mkdir()
    (bins / "python").write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    (bins / "python").chmod(0o755)
    runner = tmp_path / "runner"
    runner.mkdir()
    return {**os.environ, "PATH": f"{bins}{os.pathsep}{os.environ['PATH']}", "RUNNER_TEMP": str(runner),
            "BASE_REF": "base", "PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_CACHE_DIR": "1",
            "PYTHONPATH": os.pathsep.join(str(repo / p) for p in ("src", "scripts", "."))}


def cleanroom_block(title):
    script = (ROOT / "scripts/cleanroom.sh").read_text()
    return script.split(f'step "{title}"\n', 1)[1].split('\nstep "', 1)[0]


def run_workflow(repo, tmp_path, cleanroom=False):
    env = isolated_env(tmp_path, repo)
    if cleanroom:
        work = tmp_path / "cleanroom"
        work.mkdir()
        subprocess.run(["git", "clone", "--quiet", "--single-branch", "--branch", "candidate", str(repo), str(work / "repo")],
                       check=True, capture_output=True)
        script = (f'work={shlex.quote(str(work))}\npython={shlex.quote(sys.executable)}\nbase_branch=main\n'
                  'quiet() { "$@"; }\n' +
                  cleanroom_block("Trusted report rules from $base_branch, history comparison with the merge base") + '\n' +
                  cleanroom_block("Report sections for added or content-changed editions"))
        cwd = work / "repo"
    else:
        script, cwd = step_script(STEP), repo
    return subprocess.run(["bash", "--noprofile", "--norc", "-euo", "pipefail", "-c", script], cwd=cwd,
                          env=env, capture_output=True, text=True, timeout=120)


@pytest.mark.parametrize("cleanroom", [False, True], ids=["base-rules", "cleanroom"])
@pytest.mark.parametrize("stale", [False, True], ids=["current-report", "stale-report"])
def test_ci_and_cleanroom_use_only_base_checker_renderer_and_stdlib(tmp_path, cleanroom, stale):
    repo, marker = workflow_repo(tmp_path, stale=stale)
    result = run_workflow(repo, tmp_path, cleanroom)
    assert not marker.exists(), result.stdout + result.stderr
    assert "PR checker accepted everything" not in result.stdout
    assert (result.returncode != 0) == stale, result.stdout + result.stderr
    assert ("signed-evaluation section differs" in result.stderr) == stale
    assert ("matches render-evaluation exactly" in result.stdout) != stale


def test_pr_forked_before_the_rule_cannot_bypass_current_base_rules(tmp_path):
    repo, marker = workflow_repo(tmp_path, stale=True, behind=True)
    result = run_workflow(repo, tmp_path)
    assert result.returncode != 0 and "signed-evaluation section differs" in result.stderr
    assert not marker.exists()
    assert "no trusted checker" not in result.stdout


@pytest.mark.parametrize("cleanroom", [False, True], ids=["base-rules", "cleanroom"])
def test_bootstrap_explicitly_skips_without_ever_falling_back_to_pr_code(tmp_path, cleanroom):
    repo, marker = workflow_repo(tmp_path, bootstrap=True)
    result = run_workflow(repo, tmp_path, cleanroom)
    assert result.returncode == 0, result.stderr
    assert "no trusted checker is available yet" in result.stdout
    assert "PR checker accepted everything" not in result.stdout
    assert not marker.exists()
