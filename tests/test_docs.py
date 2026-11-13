"""The documented offline commands run exactly as written."""
import json
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


def documents(text):
    """Every JSON document that the commands printed, in order; plain lines such as echo messages are skipped."""
    decoder, found, index = json.JSONDecoder(), [], 0
    while index < len(text):
        if text[index].isspace():
            index += 1
            continue
        try:
            document, index = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            index = text.find("\n", index) + 1 or len(text)
            continue
        found.append(document)
    return found


def test_registering_before_the_first_product_runs_as_written(tmp_path):
    """CONTRIBUTING.md's two pull requests for a new author, run with the command line exactly as documented."""
    script = section_script("AUTHORING.md", "## Registering before your first product")
    for step in ("keygen", '"packages": []', '"product_ids": []', '"status": "committed"', "catalog check",
                 "--base", "catalog trust", '["packages"].append("new-product")'):
        assert step in script, step
    repo = copy_data(tmp_path / "repo")
    authors = json.loads((repo / "catalog" / "authors.json").read_text())["authors"]
    products = len(list((repo / "catalog" / "products").glob("*.json")))
    keys = sum(len(author["keys"]) for author in authors)
    before = {path: path.read_bytes() for path in repo.rglob("*") if path.is_file()}
    result = run(script, repo, install_shims(tmp_path / "bin"))
    assert result.returncode == 0, result.stderr[-3000:]
    printed = documents(result.stdout)
    checks = [document for document in printed if document.get("status") == "verified"]
    # First pull request: one more author and key, no new product; second: the first product. Both only append.
    assert [(c["authors"], c["keys"], c["products"], c["append_only"]) for c in checks] == [
        (len(authors) + 1, keys + 1, products, True), (len(authors) + 1, keys + 1, products + 1, True)]
    assert "Refused as expected: new-product is not in the catalog yet" in result.stdout
    assert "Unknown product new-product" in result.stderr
    trusts = [document for document in printed if document.get("status") == "written"]
    assert [trust["product_id"] for trust in trusts] == ["synthetic-example", "new-product"]
    assert trusts[0]["keys"] and "new-author-2020" not in trusts[0]["keys"]
    assert trusts[1]["keys"] == ["new-author-2020"] and trusts[1]["allow_paper"] is False
    assert json.loads(Path(trusts[1]["output"]).read_text())["new-author-2020"]["packages"] == ["new-product"]
    # The documented commands work in scratch copies: the checkout itself is unchanged.
    assert {path: path.read_bytes() for path in repo.rglob("*") if path.is_file()} == before
