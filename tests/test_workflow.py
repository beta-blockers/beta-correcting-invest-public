"""The base-rules job in .github/workflows/test.yml never runs code from the pull request it judges.

The job's step is taken from the workflow file and run in a fictional repository. The base branch carries a stub
checker that refuses an altered report; the pull request alters the report and plants venv.py and pip.py at its
root, which, if Python ever imported them, would replace the checker with one that accepts everything.
"""
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "test.yml"
STEP = "Catalog and history pass the base branch's checks"
NOREPLY = "12345+demo" + "@users.noreply.github.com"
pytestmark = pytest.mark.skipif(shutil.which("git") is None or shutil.which("bash") is None
                                or importlib.util.find_spec("ensurepip") is None,
                                reason="needs git, bash and ensurepip")

COMMON_STUB = '''from datetime import datetime, timezone


class Refused(ValueError):
    pass


def now():
    return datetime.now(timezone.utc)
'''
CHECKER_STUB = '''from pathlib import Path

from .common import Refused


def check(tree, now, base):
    if (Path(tree) / "history" / "REPORT.md").read_bytes() != (Path(base) / "history" / "REPORT.md").read_bytes():
        raise Refused("history/REPORT.md changed")
    return {"editions": []}
'''
PLANTED = '''"""Planted by a contributor: replace the base branch's checker, then run the real module."""
import os
import pathlib
import runpy
import sys

runner = pathlib.Path(os.environ["RUNNER_TEMP"])
with open(runner / "planted-module-ran", "a") as marker:
    marker.write(__file__ + "\\n")
checker = runner / "base" / "src" / "public_pilot" / "catalog.py"
checker.write_text("def check(tree, now, base):\\n    return {'editions': []}\\n")
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [entry for entry in sys.path if os.path.abspath(entry or os.curdir) != here]
runpy.run_module(NAME, run_name="__main__", alter_sys=True)
'''


def step_script(name):
    """The run: | script of the named workflow step, de-indented."""
    lines = WORKFLOW.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f"- name: {name}")
    run = next(i for i in range(start, len(lines)) if lines[i].strip() == "run: |")
    indent = len(lines[run + 1]) - len(lines[run + 1].lstrip())
    script = []
    for line in lines[run + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) < indent:
            break
        script.append(line[indent:])
    return "\n".join(script) + "\n"


def git(repo, *args):
    env = {**os.environ, "HOME": str(repo.parent), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_AUTHOR_NAME": "Demo", "GIT_AUTHOR_EMAIL": NOREPLY, "GIT_COMMITTER_NAME": "Demo",
           "GIT_COMMITTER_EMAIL": NOREPLY}
    return subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True)


def write(root, files):
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def run_step(tmp_path, script):
    """Run a version of the step as CI would for a pull request; return the result and RUNNER_TEMP."""
    repo, runner, shims = tmp_path / "checkout", tmp_path / "runner", tmp_path / "bin"
    for directory in (repo, runner, shims):
        directory.mkdir()
    write(repo, {"src/public_pilot/__init__.py": "", "src/public_pilot/common.py": COMMON_STUB,
                 "src/public_pilot/catalog.py": CHECKER_STUB, "catalog/authors.json": "{}\n",
                 "history/REPORT.md": "Original report.\n",
                 "requirements.lock": "# The stub checker needs no third-party package.\n"})
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Base")
    git(repo, "update-ref", "refs/remotes/origin/base", "HEAD")
    write(repo, {"history/REPORT.md": "Altered report.\n", "venv.py": PLANTED.replace("NAME", '"venv"'),
                 "pip.py": PLANTED.replace("NAME", '"pip"')})
    git(repo, "add", "-A")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Alter the report and plant modules")
    (shims / "python").write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    (shims / "python").chmod(0o755)
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTHON")}
    env.update(PATH=f"{shims}{os.pathsep}{os.environ['PATH']}", RUNNER_TEMP=str(runner), BASE_REF="base",
               PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1", PIP_NO_CACHE_DIR="1")
    result = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script], cwd=repo, env=env,
                            capture_output=True, text=True, timeout=300)
    return result, runner


def test_the_step_leaves_the_checkout_before_any_python_and_isolates_every_interpreter():
    lines = [line.strip() for line in step_script(STEP).splitlines()]
    lines = lines[:next(i for i, line in enumerate(lines) if line.endswith("<<'PY'")) + 1]  # not the heredoc body
    leave = lines.index('cd "$RUNNER_TEMP"')
    assert lines[leave - 1] == 'tree="$PWD"'
    assert not any(line.startswith(("cd ", "pushd ")) for line in lines[leave + 1:])
    calls = [i for i, line in enumerate(lines)
             if not line.startswith("#") and re.search(r'(^|[\s"/])python3?"?\s', line)]
    assert len(calls) == 3, [lines[i] for i in calls]  # create the environment, install, check
    for i in calls:
        assert i > leave, f"Python runs inside the checkout: {lines[i]}"
        assert re.search(r'python3?"?\s+-I\s', lines[i]), f"Python runs without -I: {lines[i]}"


def test_modules_planted_by_the_pull_request_never_run_and_the_base_checker_still_refuses(tmp_path):
    result, runner = run_step(tmp_path, step_script(STEP))
    output = result.stdout + result.stderr
    assert not (runner / "planted-module-ran").exists(), output
    assert (runner / "base" / "src" / "public_pilot" / "catalog.py").read_text() == CHECKER_STUB
    assert result.returncode != 0 and "Refused: history/REPORT.md changed" in output, output


def test_the_planted_modules_would_take_over_a_step_that_ran_python_inside_the_checkout(tmp_path):
    """The control for the test above: run from inside the checkout without -I, the same step is subverted."""
    script = step_script(STEP)
    vulnerable = script.replace('tree="$PWD"\ncd "$RUNNER_TEMP"\n', 'tree="$PWD"\n', 1)
    vulnerable = vulnerable.replace("python -I -m venv", "python -m venv", 1)
    vulnerable = vulnerable.replace('/bin/python" -I -m pip', '/bin/python" -m pip', 1)
    vulnerable = vulnerable.replace('"$RUNNER_TEMP/venv/bin/python" -I - ',
                                    'cd "$RUNNER_TEMP"\n"$RUNNER_TEMP/venv/bin/python" -I - ', 1)
    assert vulnerable != script and vulnerable.count('cd "$RUNNER_TEMP"') == 1 and " -I -m " not in vulnerable
    result, runner = run_step(tmp_path, vulnerable)
    ran = (runner / "planted-module-ran").read_text().splitlines()
    assert [Path(path).name for path in ran] == ["venv.py", "pip.py"]
    assert result.returncode == 0 and "accepts catalog/ and history/" in result.stdout, result.stderr
