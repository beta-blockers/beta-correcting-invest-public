"""Compare added or content-changed editions with the trusted base's render-evaluation.

Usage (outside the checkout): python -I BASE/scripts/check_report_evaluation.py BASE TREE
BASE contains trusted source and scripts, plus history from the comparison merge base.
TREE is read only as data. Signature, binding and append-only checks remain separate.
"""
import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import re
import sys


def check(report, rendered):
    """The renderer's complete output must occur once, as the report's final section."""
    headings = list(re.finditer(rb"(?m)^# Evaluation of ", report))
    if len(headings) != 1:
        raise ValueError("expected exactly one '# Evaluation of ...' section at the end of the report")
    if report[headings[0].start():] != rendered:
        raise ValueError("signed-evaluation section differs from public-pilot render-evaluation; "
                         "for a new edition, render the final evaluation before signing release.json. "
                         "Published reports must remain unchanged")


def check_editions(base, tree):
    # -I keeps the checkout and script directory off the import path. Only this trusted export's
    # source is added; never import the proposed tree's renderer, checker or Python modules.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from public_pilot.catalog import edition_content, history_editions
    from public_pilot.cli import main as cli

    checked = 0
    for product, quarter, directory in history_editions(tree):
        relative = Path("history") / product / quarter
        previous = base / relative
        # Use the same definition of content as the append-only rules: snapshot/evaluation payloads,
        # report and fixture. Key rotation changes signatures and inventory, not report content.
        if previous.is_dir() and edition_content(previous, str(relative)) == edition_content(directory, str(relative)):
            continue
        report = directory / "REPORT.md"
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                status = cli(["render-evaluation", str(directory / "evaluation.json")])
            if status:
                raise ValueError("render-evaluation failed")
            check(report.read_bytes(), output.getvalue().encode("utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"{relative}/REPORT.md: {exc}") from exc
        print(f"{relative}/REPORT.md: signed-evaluation section matches render-evaluation exactly")
        checked += 1
    if not checked:
        print("No added or content-changed editions; published reports were not re-rendered.")
    return checked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("tree", type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.base.is_dir() or not args.tree.is_dir():
            raise ValueError("base and proposed tree must both be existing directories")
        check_editions(args.base.resolve(), args.tree.resolve())
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
