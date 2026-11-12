#!/usr/bin/env bash
# Export scan. Run from anywhere inside a checkout; needs git and python3.
#
# Usage: scripts/export_scan.sh [REVISION]
#
# Passes only if:
#  1. every tracked path is inside the export allowlist;
#  2. no tracked path or file, as it is in the working tree now, contains a forbidden string
#     (this script skips itself);
#  3. every commit reachable from REVISION (default HEAD) has GitHub noreply author and committer
#     addresses. Continuous integration passes the pull request's head commit, so that the merge commit
#     GitHub proposes for a pull request, which is never published, is not judged by its address.
# Older versions of files and commit messages are not scanned: the repository is published as a fresh
# export of the tracked files of one scanned commit, never with this history.
# Findings name the file, line or commit; email addresses themselves are never printed.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
exec "${PYTHON:-python3}" - "$@" <<'PY'
import re
import subprocess
import sys

SELF = "scripts/export_scan.sh"
ALLOWED_FILES = {".github/workflows/test.yml", ".gitignore", "LICENSE", "README.md", "CONTRIBUTING.md",
                 "SECURITY.md", "MANIFEST.in", "pyproject.toml", "requirements.lock", "requirements-test.lock"}
ALLOWED_DIRECTORIES = ("src/public_pilot/", "tests/", "docs/", "schemas/", "author-kit/", "catalog/",
                       "history/", "examples/", "scripts/")
FORBIDDEN = [
    ("pbt_etf", re.compile(r"pbt_etf", re.IGNORECASE)),
    ("pbt-etf", re.compile(r"pbt-etf", re.IGNORECASE)),
    ("launch_pilot", re.compile(r"launch_pilot", re.IGNORECASE)),
    ("BUILD-STATUS", re.compile(r"BUILD-STATUS", re.IGNORECASE)),
    ("s3://", re.compile(r"s3://", re.IGNORECASE)),
    ("arn:aws", re.compile(r"arn:aws", re.IGNORECASE)),
    ("V1x version label", re.compile(r"\bV1[0-9]\b", re.IGNORECASE)),
    ("PRIVATE KEY", re.compile(r"PRIVATE KEY")),
    ("12-digit number", re.compile(r"\b[0-9]{12}\b")),
]
# The product word is assembled at run time so that no file in the repository spells it outside
# catalog/ and history/, this scanner included.
PRODUCT_WORD = "us" + "chips"
PRODUCT_PATTERN = re.compile(PRODUCT_WORD, re.IGNORECASE)
PRODUCT_ALLOWED = ("catalog/", "history/")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@((?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})")
NOREPLY_DOMAIN = "users.noreply.github.com"
GITHUB_WEB_COMMITTER = "noreply@github.com"


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def shown(where):
    """A location safe to print: any address-like text in a path is masked."""
    return EMAIL.sub("<address>", where)


def noreply(address):
    address = address.lower()
    return address.endswith("@" + NOREPLY_DOMAIN) or address == GITHUB_WEB_COMMITTER


if len(sys.argv) > 2:
    sys.exit("usage: scripts/export_scan.sh [REVISION]")
revision = sys.argv[1] if len(sys.argv) == 2 else "HEAD"
try:
    if revision.startswith("-"):
        raise ValueError(revision)
    commit = git("rev-parse", "--verify", "--quiet", revision + "^{commit}").decode().strip()
except (ValueError, subprocess.CalledProcessError):
    sys.exit(f"export scan failed: {shown(revision)} is not a commit")

problems = []
paths = [raw.decode("utf-8", "surrogateescape") for raw in git("ls-files", "-z").split(b"\0") if raw]
for path in paths:
    if path not in ALLOWED_FILES and not path.startswith(ALLOWED_DIRECTORIES):
        problems.append(f"{shown(path)}: outside the export allowlist")

for path in paths:
    if path == SELF:
        continue
    try:
        with open(path, "rb") as stream:
            text = stream.read().decode("utf-8", "replace")
    except OSError:
        problems.append(f"{shown(path)}: tracked but unreadable in the working tree")
        continue
    places = [(f"{shown(path)} (path)", path)] + [(f"{shown(path)}:{number}", line)
                                                  for number, line in enumerate(text.splitlines(), 1)]
    for where, value in places:
        for label, pattern in FORBIDDEN:
            if pattern.search(value):
                problems.append(f"{where}: forbidden string {label}")
        for match in EMAIL.finditer(value):
            if match.group(1).lower() != NOREPLY_DOMAIN:
                problems.append(f"{where}: email address that is not a GitHub noreply address")
        if not path.startswith(PRODUCT_ALLOWED) and PRODUCT_PATTERN.search(value):
            problems.append(f"{where}: {PRODUCT_WORD} outside catalog/ and history/")

for line in git("log", "--format=%H%x00%ae%x00%ce", commit).decode("utf-8", "replace").splitlines():
    commit, author, committer = line.split("\0")
    for role, address in (("author", author), ("committer", committer)):
        if not noreply(address):
            problems.append(f"commit {commit[:12]}: {role} address is not a GitHub noreply address")

for problem in problems:
    print(problem, file=sys.stderr)
if problems:
    print(f"export scan failed: {len(problems)} finding(s)", file=sys.stderr)
    sys.exit(1)
print(f"export scan passed: {len(paths)} tracked files, allowlist, forbidden strings and commit addresses")
PY
