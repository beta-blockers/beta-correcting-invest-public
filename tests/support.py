"""Shared helpers for the author-tool tests. All data is fictional."""
from datetime import datetime, timezone
import json
from pathlib import Path

from public_pilot import authoring, cli
from public_pilot.common import digest
from public_pilot.evaluation import render

SIGNED_AT = datetime(2020, 1, 2, 12, tzinfo=timezone.utc)  # inside the fictional edition's validity
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)  # long after it expired
FIXTURE = {"account_id": "synthetic-offline-account", "cash": "1000", "equity": "1000", "positions": {},
           "observed_at": "2020-01-02T15:00:00+00:00", "market_open": True, "open_orders": [],
           "quotes": {s: {"bid": "49.95", "ask": "50", "at": "2020-01-02T15:00:00+00:00"}
                      for s in ("DEMOA", "DEMOB", "DEMOC")},
           "assets": {s: {"tradable": True} for s in ("DEMOA", "DEMOB", "DEMOC")}}


def write(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n")
    return str(path)


def read(path):
    return json.loads(Path(path).read_text())


def call(capsys, argv):
    """Run the command line; return its exit code and the JSON it printed (stdout, or stderr on refusal)."""
    code = cli.main([str(a) for a in argv])
    captured = capsys.readouterr()
    return code, json.loads(captured.out if code == 0 else captured.err)


def new_key(directory, name="author.key"):
    """A fresh signing key written by keygen; returns the private key and keygen's output."""
    created = authoring.keygen(Path(directory) / name)
    return authoring.load_private_key(created["key"]), created


def trust_for(private, key_id, author_id, packages, allow_paper=False):
    return {key_id: {"public_key": authoring.public_key(private), "author_id": author_id,
                     "packages": list(packages), "allow_paper": allow_paper}}


def freeze(monkeypatch, instant):
    monkeypatch.setattr(cli, "now", lambda: instant)


def edition_payload(product="demo-product", author="demo-author"):
    """A fictional, already expired quarterly edition."""
    return {"package_id": product, "edition_id": f"{product}-2020-q1", "author_id": author, "engine_major": 1,
            "purpose": "demo", "published_at": "2020-01-02T00:00:00+00:00",
            "information_cutoff": "2019-12-31T00:00:00+00:00", "valid_until": "2020-04-01T00:00:00+00:00",
            "geographies": ["SYNTHETIC"], "policy_ids": ["fictional-policy"], "universe": ["DEMOA", "DEMOB", "DEMOC"],
            "targets": {"DEMOA": "0.45", "DEMOB": "0.35"}, "research": "Fictional research for tests.", "evidence": []}


def evaluation_payload(payload, **changes):
    def entry(rank, composite, weight, decision="include"):
        return {"rank": rank, "composite": composite, "components": {"p1": composite, "p2": "50"},
                "decision": decision, "weight": weight, "note": ""}

    return {"package_id": payload["package_id"], "edition_id": payload["edition_id"],
            "author_id": payload["author_id"], "package_sha256": digest(payload),
            "as_of": payload["information_cutoff"],
            "method": {"name": "Fictional score", "version": "1.0", "description": "Invented for tests."},
            "thresholds": {"exit_below": "40"},
            "companies": {"DEMOA": entry(1, "72", payload["targets"]["DEMOA"]),
                          "DEMOB": entry(2, "61", payload["targets"]["DEMOB"]),
                          "DEMOC": entry(3, "38", "0", "exit")},
            "defaults_disclosed": [], **changes}


def write_edition(directory, private, key_id, payload, evaluation):
    """The five files of a history directory. The evaluation is signed without a self-check."""
    directory.mkdir(parents=True)
    snapshot = authoring.sign_snapshot(private, key_id, payload, SIGNED_AT)
    authoring.write_new(directory / "edition.snapshot.json", snapshot)
    signed = authoring.sign(private, {"format": "public-pilot-evaluation-v1", "key_id": key_id, "payload": evaluation})
    authoring.write_new(directory / "evaluation.json", signed)
    (directory / "REPORT.md").write_text(render(signed))
    write(directory / "account.fixture.json", FIXTURE)
    release = authoring.sign_release(private, key_id, directory, "edition.snapshot.json", SIGNED_AT)
    authoring.write_new(directory / "release.json", release)
    return directory


def catalog_documents(private, key_id="demo-key", quarter="2020-Q1", **key_changes):
    public = authoring.public_key(private)
    key = {"key_id": key_id, "public_key": public, "fingerprint_sha256": authoring.fingerprint(public),
           "status": "active", "valid_from": "2019-06-01", "packages": ["demo-product"], **key_changes}
    themes = {"format": "public-pilot-themes-v1", "themes": [{
        "theme_id": "demo-theme", "title": "Fictional theme", "geographies": ["SYNTHETIC"],
        "policy_ids": ["fictional-policy"], "status": "researched", "author_ids": ["demo-author"],
        "product_ids": ["demo-product"], "committed_on": "2019-06-01", "latest_public_quarter": quarter}]}
    authors = {"format": "public-pilot-authors-v1", "authors": [{
        "author_id": "demo-author", "display_name": "Fictional Author", "keys": [key]}]}
    product = {"format": "public-pilot-product-v1", "product_id": "demo-product", "theme_id": "demo-theme",
               "author_id": "demo-author", "cadence": "quarterly", "universe_size": 3,
               "methodology_summary": "Fictional product for tests.", "public_history_path": "history/demo-product",
               "review_status": "author_published"}
    return themes, authors, product


def build_repository(root, private, key_id="demo-key", evaluation_changes=None, **key_changes):
    """A fictional repository: catalog files plus history/demo-product/2020-Q1."""
    themes, authors, product = catalog_documents(private, key_id, **key_changes)
    write(root / "catalog" / "themes.json", themes)
    write(root / "catalog" / "authors.json", authors)
    write(root / "catalog" / "products" / "demo-product.json", product)
    payload = edition_payload()
    write_edition(root / "history" / "demo-product" / "2020-Q1", private, key_id, payload,
                  evaluation_payload(payload, **(evaluation_changes or {})))
    return root
