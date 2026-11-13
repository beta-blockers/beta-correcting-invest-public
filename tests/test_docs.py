"""The documented offline commands run exactly as written."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


def section_script(document, heading):
    """Every ```sh block inside the level-two section with this heading, joined in order."""
    blocks, inside, block = [], False, None
    for line in (ROOT / "docs" / document).read_text().splitlines():
        if block is not None:
            if line == "```":
                blocks.append("\n".join(block))
                block = None
            else:
                block.append(line)
        elif line.startswith("## "):
            inside = line == heading
        elif inside and line == "```sh":
            block = []
    assert blocks, f"no shell blocks under {heading!r} in {document}"
    return "\n".join(blocks) + "\n"


def install_shims(directory):
    """`public-pilot` and `python` commands that run this checkout's source with this interpreter."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "public-pilot").write_text(
        f'#!/bin/sh\nPYTHONPATH="{ROOT / "src"}" exec "{sys.executable}" -m public_pilot "$@"\n')
    (directory / "python").write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    for name in ("public-pilot", "python"):
        (directory / name).chmod(0o755)
    return directory


def run(script, cwd, shims):
    env = {**os.environ, "PATH": f"{shims}{os.pathsep}{os.environ['PATH']}", "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(["bash", "-euo", "pipefail", "-c", script], cwd=cwd, env=env, capture_output=True,
                          text=True, timeout=300)


def copy_data(target):
    for name in ("author-kit", "catalog", "examples", "history"):
        shutil.copytree(ROOT / name, target / name)
    return target


def test_engine_fictional_example_runs_as_written(tmp_path):
    script = section_script("ENGINE.md", "## Try the fictional example without credentials")
    repo = copy_data(tmp_path / "repo")
    result = run(script, repo, install_shims(repo / ".venv" / "bin"))
    assert result.returncode == 0, result.stderr[-3000:]
    assert '"orders_submitted": 0' in result.stdout


def test_authoring_walkthrough_runs_as_written_and_passes_the_checks(tmp_path):
    script = section_script("AUTHORING.md", "## Walkthrough")
    for step in ("keygen", "validate ", "sign snapshot", "sign-evaluation", "sign release", "verify-bundle",
                 "verify-evaluation", "catalog check", "validate-news-config", "sign delta", "resign-edition",
                 "--base"):
        assert step in script, step
    repo = copy_data(tmp_path / "repo")
    result = run(script, repo, install_shims(tmp_path / "bin"))
    assert result.returncode == 0, result.stderr[-3000:]
    assert result.stdout.count('"status": "verified"') >= 3 and '"expired": true' in result.stdout
    assert '"status": "re-signed"' in result.stdout and '"append_only": true' in result.stdout
    assert "Refused as expected" in result.stdout and "Publisher is not in the local trust store" in result.stderr
    assert sorted(path.name for path in (repo / "catalog").iterdir()) == ["authors.json", "products", "themes.json"]


@pytest.mark.parametrize("shell", ["bash", "sh", "zsh"])
def test_public_sample_walkthrough_runs_as_written(tmp_path, shell):
    if shutil.which(shell) is None:
        pytest.skip(f"needs {shell}")
    script = section_script("SAMPLE.md", "## Preview locally")
    repo = copy_data(tmp_path / "repo")
    install_shims(repo / ".venv" / "bin")
    # Do not add shell safety options: the pasted block must supply its own.
    result = subprocess.run([shell, "-c", script], cwd=repo, capture_output=True,
                            text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-3000:]
    assert result.stdout.count('"status": "verified"') >= 2
    assert '"purpose": "demo"' in result.stdout
    assert '"offline": true' in result.stdout and '"orders_submitted": 0' in result.stdout
    trust_files = list((repo / ".state").glob("*/trust.json"))
    assert len(trust_files) == 1
    assert '"allow_paper": false' in trust_files[0].read_text()


@pytest.mark.parametrize("shell", ["bash", "sh", "zsh"])
def test_public_sample_walkthrough_stops_before_install_after_tampering(tmp_path, shell):
    if shutil.which(shell) is None:
        pytest.skip(f"needs {shell}")
    repo = copy_data(tmp_path / "repo")
    bins = install_shims(repo / ".venv" / "bin")
    report = repo / "history" / ("us" + "chips") / "2026-Q4" / "REPORT.md"
    report.write_text(report.read_text() + "\nTampered.\n")
    command = bins / "public-pilot"
    original = command.read_text()
    command.write_text(original.replace("PYTHONPATH=", 'printf "%s\\n" "$*" >> calls.log\nPYTHONPATH=', 1))
    result = subprocess.run([shell, "-c", section_script("SAMPLE.md", "## Preview locally")],
                            cwd=repo, capture_output=True, text=True, timeout=120)
    assert result.returncode != 0
    calls = (repo / "calls.log").read_text().splitlines()
    assert len(calls) == 2 and "verify-bundle" in calls[-1]
    assert "offline preview passed" not in result.stdout
    assert not list((repo / ".state").glob("*/state"))


def test_evidence_companion_identifies_the_actual_sample_payload():
    import json
    from public_pilot.common import digest

    product = "us" + "chips"
    edition = ROOT / "history" / product / "2026-Q4"
    envelope = json.loads((edition / "edition.snapshot.json").read_text())
    companion_name = product.upper() + "-Q4-2026-EVIDENCE-20261112.md"
    companion = (ROOT / "docs" / companion_name).read_text()
    assert digest(envelope["payload"]) in companion
    assert envelope["payload"]["edition_id"] in companion
    assert companion_name in (ROOT / "docs" / "SAMPLE.md").read_text()
    assert companion_name in (ROOT / "README.md").read_text()
