"""scripts/export_scan.sh: export allowlist, forbidden strings and commit addresses.

Forbidden strings are assembled at run time so that this file itself never contains them.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "export_scan.sh"
NOREPLY = "12345+demo" + "@users.noreply.github.com"
PERSONAL = "someone" + "@" + "example.org"
pytestmark = pytest.mark.skipif(shutil.which("git") is None or shutil.which("bash") is None,
                                reason="needs git and bash")


def git(repo, *args, author=NOREPLY, committer=None):
    env = {**os.environ, "HOME": str(repo.parent), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_AUTHOR_NAME": "Demo", "GIT_AUTHOR_EMAIL": author,
           "GIT_COMMITTER_NAME": "Demo", "GIT_COMMITTER_EMAIL": committer or author}
    return subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True)


def commit(repo, author=NOREPLY, committer=None):
    git(repo, "add", "-A")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "Fictional change",
        author=author, committer=committer)


def scan(repo):
    return subprocess.run(["bash", str(repo / "scripts" / "export_scan.sh")], cwd=repo, capture_output=True,
                          text=True, env={**os.environ, "PYTHON": sys.executable}, timeout=120)


def add(repo, relative, text):
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    commit(repo)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    (path / "scripts").mkdir(parents=True)
    shutil.copy(SCANNER, path / "scripts" / "export_scan.sh")
    (path / "README.md").write_text("# Fictional repository\n")
    (path / "docs").mkdir()
    (path / "docs" / "ENGINE.md").write_text("Fictional documentation.\n")
    git(path, "init", "-q")
    commit(path)
    return path


def test_clean_repository_passes_and_the_scanner_skips_itself(repo):
    assert "PRIVATE" + " KEY" in SCANNER.read_text()
    result = scan(repo)
    assert result.returncode == 0, result.stderr
    assert "export scan passed" in result.stdout


@pytest.mark.parametrize("relative", ["notes.txt", ".github/workflows/deploy.yml", "publisher/sign.py",
                                      "src/other_package/module.py", ".env.example", "ARCHITECTURE.md"])
def test_a_file_outside_the_allowlist_fails(repo, relative):
    add(repo, relative, "fictional\n")
    result = scan(repo)
    assert result.returncode == 1 and f"{relative}: outside the export allowlist" in result.stderr


WORD = "us" + "chips"
FORBIDDEN = [  # (scanner label, seeded line)
    ("pbt" + "_etf", "import " + "pbt" + "_etf"),
    ("pbt" + "-etf", "github.com/someone/" + "pbt" + "-etf"),
    ("launch" + "_pilot", "launch" + "_pilot/run.sh"),
    ("BUILD" + "-STATUS", "see " + "BUILD" + "-STATUS.md"),
    ("s3" + "://", "s3" + "://bucket/key"),
    ("arn" + ":aws", "arn" + ":aws:iam::role/name"),
    ("V1x version label", "the " + "V" + "15 deployment"),
    ("V1x version label", "the " + "v" + "18 runner"),
    ("PRIVATE" + " KEY", "-----BEGIN " + "PRIVATE" + " KEY-----"),
    ("12-digit number", "account " + "1234" * 3),
]


@pytest.mark.parametrize("label, line", FORBIDDEN)
def test_each_forbidden_string_fails(repo, label, line):
    add(repo, "docs/notes.md", f"Fictional text.\n{line}\n")
    result = scan(repo)
    assert result.returncode == 1 and f"docs/notes.md:2: forbidden string {label}" in result.stderr


def test_an_email_address_other_than_noreply_fails_without_being_printed(repo):
    add(repo, "docs/notes.md", f"Fictional text.\ncontact {PERSONAL}\n")
    result = scan(repo)
    assert result.returncode == 1 and "docs/notes.md:2: email address that is not a GitHub noreply" in result.stderr
    assert PERSONAL not in result.stderr


def test_forbidden_strings_in_paths_fail(repo):
    add(repo, "docs/" + "pbt" + "_etf.md", "fictional\n")
    result = scan(repo)
    assert result.returncode == 1 and "(path): forbidden string " + "pbt" + "_etf" in result.stderr


def test_noreply_addresses_are_allowed_in_files(repo):
    add(repo, "docs/notes.md", f"Commits use {NOREPLY}.\n")
    assert scan(repo).returncode == 0


def test_the_product_word_is_allowed_only_under_catalog_and_history(repo):
    add(repo, f"catalog/products/{WORD}-q4.json", f'{{"product_id": "{WORD}-q4"}}\n')
    add(repo, f"history/{WORD}-q4/2026-Q4/REPORT.md", f"# {WORD.upper()}\n")
    assert scan(repo).returncode == 0
    add(repo, "docs/notes.md", f"The {WORD.upper()} product.\n")
    result = scan(repo)
    assert result.returncode == 1 and f"docs/notes.md:1: {WORD} outside catalog/ and history/" in result.stderr
    (repo / "docs" / "notes.md").unlink()
    add(repo, f"examples/{WORD}.json", "{}\n")
    result = scan(repo)
    assert result.returncode == 1 and f"examples/{WORD}.json (path): {WORD} outside" in result.stderr


@pytest.mark.parametrize("author, committer, role", [
    (PERSONAL, NOREPLY, "author"), (NOREPLY, PERSONAL, "committer"),
])
def test_a_commit_with_a_non_noreply_address_fails(repo, author, committer, role):
    commit(repo, author=author, committer=committer)
    result = scan(repo)
    assert result.returncode == 1 and f"{role} address is not a GitHub noreply address" in result.stderr
    assert PERSONAL not in result.stderr


def test_github_web_commits_use_an_accepted_noreply_committer(repo):
    commit(repo, author=NOREPLY, committer="noreply" + "@github.com")
    assert scan(repo).returncode == 0


def test_this_repository_passes_the_export_scan():
    if not (ROOT / ".git").exists():
        pytest.skip("not a Git checkout")
    result = subprocess.run(["bash", str(SCANNER)], cwd=ROOT, capture_output=True, text=True,
                            env={**os.environ, "PYTHON": sys.executable}, timeout=120)
    assert result.returncode == 0, result.stderr


def test_addresses_in_file_paths_are_masked_in_the_findings(repo):
    add(repo, f"docs/notes-{PERSONAL}.md", "fictional\n")
    result = scan(repo)
    assert result.returncode == 1 and PERSONAL not in result.stderr
    assert "<address> (path): email address that is not a GitHub noreply address" in result.stderr


def scan_at(repo, *revision):
    return subprocess.run(["bash", str(repo / "scripts" / "export_scan.sh"), *revision], cwd=repo,
                          capture_output=True, text=True, env={**os.environ, "PYTHON": sys.executable}, timeout=120)


def test_the_commit_check_can_cover_a_named_commit_instead_of_head(repo):
    """CI scans the pull request's head commit; GitHub's proposed merge on top of it is never published."""
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    git(repo, "checkout", "-q", "-b", "proposed-merge")
    commit(repo, author=PERSONAL, committer="noreply" + "@github.com")
    assert scan_at(repo).returncode == 1
    result = scan_at(repo, head)
    assert result.returncode == 0, result.stderr
    add(repo, "notes.txt", "fictional\n")  # the working tree is still scanned in full
    result = scan_at(repo, head)
    assert result.returncode == 1 and "notes.txt: outside the export allowlist" in result.stderr


@pytest.mark.parametrize("revision", ["no-such-commit", "--output=elsewhere", "HEAD^{tree}"])
def test_a_revision_that_is_not_a_commit_fails(repo, revision):
    result = scan_at(repo, revision)
    assert result.returncode == 1 and "is not a commit" in result.stderr
    assert not (repo / "elsewhere").exists()


COMPANION = "docs/" + WORD.upper() + "-Q4-2026-EVIDENCE-20261112.md"
READING_REPORT = "docs/" + WORD.upper() + "-Q4-2026-REPORT-20261113.md"


@pytest.mark.parametrize("relative", ["README.md", "docs/SAMPLE.md"])
def test_public_sample_entry_points_can_name_the_product(repo, relative):
    add(repo, relative, f"Read the {WORD.upper()} sample.\n")
    result = scan(repo)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("relative", [COMPANION, READING_REPORT])
def test_removed_companion_paths_have_no_export_exception(repo, relative):
    # The path itself is refused even when the file's contents do not name the product.
    add(repo, relative, "# A document without a product label.\n")
    result = scan(repo)
    assert result.returncode == 1
    assert f"{relative} (path): {WORD} outside catalog/ and history/" in result.stderr


@pytest.mark.parametrize("relative", ["README.md", "docs/SAMPLE.md", COMPANION, READING_REPORT])
def test_public_sample_entry_points_keep_sensitive_content_checks(repo, relative):
    secret_marker = "PRIVATE" + " KEY"
    add(repo, relative, f"{WORD.upper()}\n{secret_marker}\n{PERSONAL}\n")
    result = scan(repo)
    assert result.returncode == 1
    assert f"{relative}:2: forbidden string {secret_marker}" in result.stderr
    assert f"{relative}:3: email address that is not a GitHub noreply" in result.stderr
    assert PERSONAL not in result.stderr


@pytest.mark.parametrize("relative", ["docs/SAMPLE-extra.md", "docs/README.md",
                                      COMPANION.replace("20261112", "20261113"),
                                      READING_REPORT.replace("20261113", "20261114"),
                                      READING_REPORT + ".backup",
                                      "docs/nested/" + COMPANION.removeprefix("docs/"),
                                      COMPANION + ".backup"])
def test_product_documentation_exceptions_are_exact_paths(repo, relative):
    add(repo, relative, f"{WORD.upper()}\n")
    result = scan(repo)
    assert result.returncode == 1 and f"{relative}:1: {WORD} outside" in result.stderr


@pytest.mark.parametrize("label, line", FORBIDDEN)
@pytest.mark.parametrize("relative", [COMPANION, READING_REPORT])
def test_evidence_companion_keeps_every_forbidden_content_check(repo, label, line, relative):
    add(repo, relative, f"{WORD.upper()} evidence.\n{line}\n")
    result = scan(repo)
    assert result.returncode == 1
    assert f"{relative}:2: forbidden string {label}" in result.stderr
