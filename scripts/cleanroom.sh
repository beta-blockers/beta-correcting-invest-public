#!/usr/bin/env bash
# Clean-room check: a fresh clone, a new virtual environment, and the full offline verification.
#
# Usage: scripts/cleanroom.sh [REPOSITORY_URL] [BRANCH] [BASE_BRANCH]
#   REPOSITORY_URL defaults to this checkout's origin remote; BRANCH defaults to main.
#   BASE_BRANCH defaults to main; its trusted checker and renderer judge changed research.
#   PYTHON selects the interpreter (default python3). KEEP=1 keeps the work directory.
#
# Installing from the lock files needs the package index; every later step is offline. Broker
# credentials are removed from the environment, and nothing under "Manual steps with your own paper
# account" in docs/ENGINE.md is run.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
url="${1:-$(git -C "$here" remote get-url origin)}"
branch="${2:-main}"
base_branch="${3:-main}"
python="${PYTHON:-python3}"
unset APCA_API_KEY_ID APCA_API_SECRET_KEY
work="$(mktemp -d)"
cleanup() {
  if [ "${KEEP:-0}" = 1 ]; then echo "Work directory kept: $work"; else rm -rf -- "${work:?}"; fi
}
trap cleanup EXIT
mkdir "$work/tmp"
export TMPDIR="$work/tmp"  # the authoring walkthrough's temporary key and workspace land here

step() { printf '\n== %s\n' "$*"; }

quiet() {  # run a command, showing its output only if it fails
  local log="$work/step.log"
  if ! "$@" > "$log" 2>&1; then
    cat "$log"
    echo "Clean room failed at: $*" >&2
    exit 1
  fi
}

section() {  # every ```sh block in the level-two section titled $2 of the Markdown file $1
  awk -v want="$2" '
    block && /^```$/ { block = 0; next }
    block { print; next }
    /^## / { inside = ($0 == want); next }
    inside && /^```sh$/ { block = 1 }' "$1"
}

run_section() {
  local script
  script="$(section "$1" "$2")"
  if [ -z "$script" ]; then
    echo "No commands under '$2' in $1" >&2
    exit 1
  fi
  quiet bash -euo pipefail -c "$script"
  echo "   $(printf '%s\n' "$script" | grep -c 'public-pilot') public-pilot commands passed"
}

step "Fresh clone of $branch"
git clone --quiet --single-branch --branch "$branch" -- "$url" "$work/repo"
cd "$work/repo"
git log -1 --format='   %H %s'

step "Trusted report rules from $base_branch, history comparison with the merge base"
git fetch --quiet origin "$base_branch:refs/remotes/origin/$base_branch"
rules_commit="$(git rev-parse "refs/remotes/origin/$base_branch")"
base_commit="$(git merge-base "$rules_commit" HEAD)"
report_base="$work/report-base"
mkdir -p "$report_base"
if git cat-file -e "$rules_commit:scripts/check_report_evaluation.py" 2>/dev/null; then
  git archive "$rules_commit" src requirements.lock scripts/check_report_evaluation.py | tar -x -C "$report_base"
  if git cat-file -e "$base_commit:history" 2>/dev/null; then
    git archive "$base_commit" history | tar -x -C "$report_base"
  fi
  (
    cd "$work"
    "$python" -I -m venv "$work/report-venv"
    quiet "$work/report-venv/bin/python" -I -m pip install --disable-pip-version-check -r "$report_base/requirements.lock"
  )
fi

step "New virtual environment with $("$python" --version 2>&1), installed from the lock files"
"$python" -m venv .venv
quiet .venv/bin/python -m pip install --disable-pip-version-check -r requirements-test.lock
quiet .venv/bin/python -m pip install --disable-pip-version-check --no-deps --no-build-isolation .

step "Full test suite"
.venv/bin/python -m pytest -q -p no:cacheprovider

step "Fictional example in docs/ENGINE.md"
run_section docs/ENGINE.md "## Try the fictional example without credentials"

step "Real sample preview in docs/SAMPLE.md (commands as written)"
quiet bash -c "$(section docs/SAMPLE.md '## Preview locally')"
echo "   signature, payload hash, evaluation and offline preview passed"

step "Authoring walkthrough in docs/AUTHORING.md (key in a temporary directory)"
run_section docs/AUTHORING.md "## Walkthrough"

step "Catalog check"
quiet .venv/bin/public-pilot catalog check
echo "   passed"

step "verify-bundle and verify-evaluation for every history directory"
shopt -s nullglob
editions=(history/*/*/)
if [ "${#editions[@]}" -eq 0 ]; then
  echo "   no history directories"
fi
for edition in "${editions[@]}"; do
  edition="${edition%/}"
  product="$(basename "$(dirname "$edition")")"
  trust="$work/trust-$product-$(basename "$edition").json"
  quiet .venv/bin/public-pilot catalog trust --product "$product" --out "$trust"
  quiet .venv/bin/public-pilot --trust "$trust" verify-bundle "$edition"
  quiet .venv/bin/public-pilot --trust "$trust" verify-evaluation "$edition/evaluation.json" \
    --snapshot "$edition/edition.snapshot.json"
  echo "   $edition passed"
done

step "Report sections for added or content-changed editions"
if [ -f "$report_base/scripts/check_report_evaluation.py" ]; then
  (
    cd "$work"
    quiet "$work/report-venv/bin/python" -I "$report_base/scripts/check_report_evaluation.py" \
      "$report_base" "$work/repo"
  )
  echo "   passed with the base branch's checker and renderer"
else
  echo "   the base branch predates the report comparison; no trusted checker is available yet"
fi

step "History index is current"
quiet .venv/bin/public-pilot history index --check
echo "   passed"

step "Export scan"
PYTHON=.venv/bin/python scripts/export_scan.sh

step "Clean room passed: $branch with $(.venv/bin/python --version)"
