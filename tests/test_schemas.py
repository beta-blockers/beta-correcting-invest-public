"""JSON Schemas express structure only; the Python validators stay authoritative.

(a) On a shared fixture set, every document the Python validator accepts is accepted by the schema, and
every document that breaks a structural rule is rejected by both.
(b) Relational and time-based rules are tested against the Python validator alone, with documents the
schema accepts and the engine refuses.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator
import pytest
from referencing import Registry, Resource

from conftest import delta_for
from public_pilot import authoring, bundles, catalog, newsconfig
from public_pilot.common import Refused, digest
from public_pilot.evaluation import verify_evaluation
from public_pilot.packages import resolve_chain, validate_payload
from support import (NOW, SIGNED_AT, catalog_documents, edition_payload, evaluation_payload, trust_for, write,
                     write_edition)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
NAMES = ["snapshot-payload", "delta-payload", "envelope", "trust", "evaluation", "release", "news-config",
         "themes", "authors", "product"]
REGISTRY = Registry().with_resources(
    (path.name, Resource.from_contents(json.loads(path.read_text()))) for path in SCHEMAS.glob("*.schema.json"))
KEY = Ed25519PrivateKey.generate()
TRUST = trust_for(KEY, "demo-key", "demo-author", ["demo-product"], allow_paper=True)
PAYLOAD = edition_payload()
EARLY = "2020-01-02T06:00:00+00:00"  # a later publication that is still before SIGNED_AT
NEWS = json.loads((ROOT / "author-kit" / "news-config.template.json").read_text())
NEWS_PAYLOAD = json.loads((ROOT / "author-kit" / "payload.template.json").read_text())


def schema(name):
    return Draft202012Validator(json.loads((SCHEMAS / f"{name}.schema.json").read_text()), registry=REGISTRY)


def accepted(check, document):
    try:
        check(document)
        return True
    except ValueError:  # Refused, or urllib's ValueError for a malformed URL
        return False


def envelope(payload, kind="snapshot"):
    return authoring.envelope(KEY, "demo-key", payload, kind)


def changed(document, change):
    result = deepcopy(document)
    change(result)
    return result


def chain_check(document):
    if isinstance(document, dict) and document.get("kind") == "delta":
        return resolve_chain([envelope(PAYLOAD), document], TRUST, SIGNED_AT)
    return resolve_chain([document], TRUST, SIGNED_AT)


def signed_evaluation(payload):
    return authoring.sign(KEY, {"format": "public-pilot-evaluation-v1", "key_id": "demo-key", "payload": payload})


def release_document():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "bundle"
        write_edition(root, KEY, "demo-key", PAYLOAD, evaluation_payload(PAYLOAD))
        return json.loads((root / "release.json").read_text())


def product_check(document):
    """Every product rule, structural and relational, through catalog check's static pass."""
    themes, authors, _ = catalog_documents(KEY)
    with tempfile.TemporaryDirectory() as directory:
        write(Path(directory) / "catalog" / "themes.json", themes)
        write(Path(directory) / "catalog" / "authors.json", authors)
        name = document.get("product_id", "x") if isinstance(document, dict) else "x"
        write(Path(directory) / "catalog" / "products" / f"{name}.json", document)
        catalog.check_static(directory)


THEMES, AUTHORS, PRODUCT = catalog_documents(KEY)
DELTA = delta_for(PAYLOAD, edition_id="demo-product-2020-q1-r2", published_at=EARLY)
EVALUATION = signed_evaluation(evaluation_payload(PAYLOAD))
RELEASE = release_document()
SECOND_KEY = authoring.public_key(Ed25519PrivateKey.generate())
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
NONCANONICAL_KEY = SECOND_KEY[:42] + B64[B64.index(SECOND_KEY[42]) | 1] + "="  # same 32 bytes, other spelling
EVIDENCE = {"title": "Fictional notice", "url": "https://example.com/notice", "published_at": "2019-12-01T00:00:00+00:00"}

CHECKS = {
    "snapshot-payload": lambda d: validate_payload(d, SIGNED_AT),
    "delta-payload": lambda d: resolve_chain([envelope(PAYLOAD), envelope(d, "delta")], TRUST, SIGNED_AT),
    "envelope": chain_check,
    "trust": catalog.validate_trust,
    "evaluation": lambda d: verify_evaluation(d, envelope(PAYLOAD), TRUST, NOW),
    "release": bundles.validate_release,
    "news-config": newsconfig.validate_news_config,
    "themes": catalog.validate_themes,
    "authors": catalog.validate_authors,
    "product": product_check,
}

VALID = {
    "snapshot-payload": [PAYLOAD, {**PAYLOAD, "evidence": [EVIDENCE]}, {**PAYLOAD, "targets": {"DEMOA": 1}},
                         {**PAYLOAD, "targets": {"DEMOA": "4.5E-1", "DEMOB": " 0.35 "}},
                         {**PAYLOAD, "evidence": [{**EVIDENCE, "url": " HTTPS://example.com/upper-case"}]},
                         {**PAYLOAD, "evidence": [{**EVIDENCE, "url": "ht\ttps://example.com/tab-is-removed"}]}],
    "delta-payload": [DELTA, delta_for(PAYLOAD, edition_id="r3", published_at=EARLY, targets={"DEMOA": "0.5"})],
    "envelope": [envelope(PAYLOAD), envelope(DELTA, "delta")],
    "trust": [TRUST, {}, {"k": {**TRUST["demo-key"], "public_key": NONCANONICAL_KEY}}],
    "evaluation": [EVALUATION],
    "release": [RELEASE],
    "news-config": [NEWS],
    "themes": [THEMES, {**THEMES, "themes": []}],
    # A key may list no products: an author registered with a theme before their first product.
    "authors": [AUTHORS, changed(AUTHORS, lambda d: d["authors"][0]["keys"][0].update(packages=[]))],
    "product": [PRODUCT],
}

STRUCTURAL = {
    "snapshot-payload": [
        {k: v for k, v in PAYLOAD.items() if k != "research"}, {**PAYLOAD, "run_command": "x"},
        {**PAYLOAD, "engine_major": 2}, {**PAYLOAD, "engine_major": True}, {**PAYLOAD, "purpose": "live"},
        {**PAYLOAD, "edition_id": "bad id"}, {**PAYLOAD, "edition_id": "trailing\n"},
        {**PAYLOAD, "universe": ["demoa"]}, {**PAYLOAD, "universe": ["DEMOA", "DEMOA"]},
        {**PAYLOAD, "geographies": []}, {**PAYLOAD, "targets": {}}, {**PAYLOAD, "targets": {"DEMOA": 0.5}},
        {**PAYLOAD, "targets": {"DEMOA": True}}, {**PAYLOAD, "targets": {"DEMOA": 2}},
        {**PAYLOAD, "targets": {"demoa": "0.1"}}, {**PAYLOAD, "research": ["x"]},
        {**PAYLOAD, "research": "x" * 500_001}, {**PAYLOAD, "published_at": "2020-01-02T00:00:00.000000000000000000+00:00"},
        {**PAYLOAD, "evidence": [{**EVIDENCE, "fetch": True}]},
        {**PAYLOAD, "evidence": [{**EVIDENCE, "url": "http://example.com/notice"}]},
        {**PAYLOAD, "evidence": [{**EVIDENCE, "title": ""}]}, ["not", "an", "object"]],
    "delta-payload": [
        {**DELTA, "replace": {"purpose": "paper"}}, {**DELTA, "replace": {"unknown": 1}}, {**DELTA, "replace": {}},
        {k: v for k, v in DELTA.items() if k != "result_sha256"}, {**DELTA, "base_sha256": DELTA["base_sha256"].upper()},
        {**DELTA, "package_id": "bad id"}, {**DELTA, "replace": {"targets": {"DEMOA": 0.5}}}],
    "envelope": [
        {k: v for k, v in envelope(PAYLOAD).items() if k != "signature"}, {**envelope(PAYLOAD), "format": "v2"},
        {**envelope(PAYLOAD), "kind": "patch"}, {**envelope(PAYLOAD), "signature": "!!!"},
        {**envelope(PAYLOAD), "reviewer": "x"}, envelope({k: v for k, v in PAYLOAD.items() if k != "targets"}),
        envelope({**DELTA, "replace": {}}, "delta")],
    "trust": [
        {"k": {**TRUST["demo-key"], "allow_paper": "no"}}, {"k": {**TRUST["demo-key"], "packages": "demo-product"}},
        {"k": {**TRUST["demo-key"], "extra": 1}}, {"k": {**TRUST["demo-key"], "public_key": "short"}},
        {"k": {**TRUST["demo-key"], "author_id": "bad id"}}, []],
    "evaluation": [
        changed(EVALUATION, lambda d: d["payload"]["companies"]["DEMOA"].update(rank=0)),
        changed(EVALUATION, lambda d: d["payload"]["companies"]["DEMOA"].update(rank="1")),
        changed(EVALUATION, lambda d: d["payload"]["companies"]["DEMOA"].update(composite=72)),
        changed(EVALUATION, lambda d: d["payload"]["companies"]["DEMOA"].update(composite="7e1")),
        changed(EVALUATION, lambda d: d["payload"]["companies"]["DEMOA"].update(decision="buy")),
        changed(EVALUATION, lambda d: d["payload"]["companies"]["DEMOA"].update(weight="1.5")),
        changed(EVALUATION, lambda d: d["payload"]["companies"]["DEMOA"].update(
            components={f"c{i}": "1" for i in range(41)})),
        changed(EVALUATION, lambda d: d["payload"]["companies"]["DEMOA"].pop("note")),
        changed(EVALUATION, lambda d: d["payload"]["method"].update(name="")),
        changed(EVALUATION, lambda d: d["payload"].update(thresholds={"exit_below": 40})),
        changed(EVALUATION, lambda d: d["payload"].update(extra=1)),
        changed(EVALUATION, lambda d: d.update(format="v0")), changed(EVALUATION, lambda d: d.update(signature="x"))],
    "release": [
        changed(RELEASE, lambda d: d["files"].update({"../outside": "0" * 64})),
        changed(RELEASE, lambda d: d["files"].update({"/etc/hosts": "0" * 64})),
        changed(RELEASE, lambda d: d["files"].update({"a/./b": "0" * 64})),
        changed(RELEASE, lambda d: d["files"].update({"release.json": "0" * 64})),
        changed(RELEASE, lambda d: d["files"].update({"REPORT.md": "A" * 64})),
        changed(RELEASE, lambda d: d.update(files={})), changed(RELEASE, lambda d: d.update(format="v0")),
        changed(RELEASE, lambda d: d.update(snapshot="../edition.snapshot.json")),
        changed(RELEASE, lambda d: d.update(extra=1))],
    "news-config": [
        {**NEWS, "thresholds": {"buy": "1"}}, {**NEWS, "prompt": "x"}, {**NEWS, "monitor_from": "2020/04/01"},
        {**NEWS, "timezone": "New York"}, changed(NEWS, lambda c: c["symbols"]["DEMOA"].update(cik=-1)),
        changed(NEWS, lambda c: c["symbols"]["DEMOA"].update(cik="1")),
        changed(NEWS, lambda c: c["symbols"]["DEMOA"].update(aliases=[])),
        changed(NEWS, lambda c: c["symbols"]["DEMOA"].update(aliases=["a"] * 2)),
        changed(NEWS, lambda c: c["sources"].update({"Bad Name": {"enabled": True}})),
        changed(NEWS, lambda c: c["sources"]["example-filings"].update(enabled="yes")),
        {**NEWS, "symbols": {}}, {**NEWS, "sources": {}}],
    "themes": [
        changed(THEMES, lambda d: d["themes"][0].update(status="planned")),
        changed(THEMES, lambda d: d["themes"][0].pop("title")),
        changed(THEMES, lambda d: d["themes"][0].update(committed_on="1 June 2019")),
        changed(THEMES, lambda d: d["themes"][0].update(latest_public_quarter="2020Q1")),
        changed(THEMES, lambda d: d["themes"][0].update(author_ids=["a", "a"])), {**THEMES, "extra": 1}],
    "authors": [
        changed(AUTHORS, lambda d: d["authors"][0]["keys"][0].update(status="lost")),
        changed(AUTHORS, lambda d: d["authors"][0]["keys"][0].update(public_key="not-a-key")),
        changed(AUTHORS, lambda d: d["authors"][0]["keys"][0].update(public_key=NONCANONICAL_KEY)),
        changed(AUTHORS, lambda d: d["authors"][0]["keys"][0].update(fingerprint_sha256="A" * 64)),
        changed(AUTHORS, lambda d: d["authors"][0].update(keys=[])), {**AUTHORS, "format": "v0"}],
    "product": [
        {**PRODUCT, "review_status": "reviewed"}, {**PRODUCT, "universe_size": 0}, {**PRODUCT, "cadence": "monthly"},
        {**PRODUCT, "extra": 1}, {**PRODUCT, "public_history_path": "elsewhere/demo-product"},
        {**PRODUCT, "methodology_summary": ""}],
}

RELATIONAL = {
    "snapshot-payload": [
        {**PAYLOAD, "valid_until": "2020-01-02T01:00:00+00:00"}, {**PAYLOAD, "information_cutoff": "2020-01-03T00:00:00+00:00"},
        {**PAYLOAD, "targets": {"DEMOA": "0.6", "DEMOB": "0.6"}}, {**PAYLOAD, "targets": {"DEMOZ": "0.1"}},
        {**PAYLOAD, "targets": {"DEMOA": "NaN"}}, {**PAYLOAD, "targets": {"DEMOA": "abc"}},
        {**PAYLOAD, "targets": {"DEMOA": "1.5"}}, {**PAYLOAD, "published_at": "2020-01-02T00:00:00"},
        {**PAYLOAD, "published_at": "yesterday"}, {**PAYLOAD, "evidence": [{**EVIDENCE, "published_at": "2020-01-01T00:00:00+00:00"}]},
        {**PAYLOAD, "evidence": [{**EVIDENCE, "url": "https://user:secret" + "@example.com/notice"}]}],
    "delta-payload": [
        {**DELTA, "base_sha256": "0" * 64}, {**DELTA, "result_sha256": "0" * 64},
        delta_for(PAYLOAD, edition_id="r4"),
        delta_for(PAYLOAD, published_at=EARLY), {**DELTA, "package_id": "other-product"}],
    "envelope": [
        {**envelope(PAYLOAD), "signature": "A" * 86 + "=="}, {**envelope(PAYLOAD), "key_id": "unknown-key"},
        envelope({**PAYLOAD, "valid_until": "2020-01-02T01:00:00+00:00"})],
    "evaluation": [
        signed_evaluation(evaluation_payload(PAYLOAD, package_sha256=digest({**PAYLOAD, "research": "other"}))),
        signed_evaluation(changed(evaluation_payload(PAYLOAD), lambda p: p["companies"]["DEMOA"].update(weight="0.4"))),
        signed_evaluation(changed(evaluation_payload(PAYLOAD), lambda p: p["companies"]["DEMOA"].update(rank=2))),
        signed_evaluation(changed(evaluation_payload(PAYLOAD), lambda p: p["companies"]["DEMOA"].update(composite="1"))),
        signed_evaluation(changed(evaluation_payload(PAYLOAD), lambda p: p["companies"].pop("DEMOC"))),
        signed_evaluation(evaluation_payload(PAYLOAD, as_of="yesterday")),
        signed_evaluation(evaluation_payload(PAYLOAD, edition_id="another-edition"))],
    "release": [changed(RELEASE, lambda d: d.update(snapshot="missing.json"))],
    "news-config": [
        {**NEWS, "monitor_from": "2020-07-01"}, {**NEWS, "timezone": "Mars/Olympus_Mons"},
        {**NEWS, "epoch_end": "2020-02-30"}],
    "themes": [changed(THEMES, lambda d: d["themes"].append(deepcopy(d["themes"][0]))),
               changed(THEMES, lambda d: d["themes"][0].update(committed_on="2019-02-30"))],
    "authors": [
        changed(AUTHORS, lambda d: d["authors"][0]["keys"].append({**d["authors"][0]["keys"][0], "public_key": SECOND_KEY})),
        changed(AUTHORS, lambda d: d["authors"][0]["keys"].append({**d["authors"][0]["keys"][0], "key_id": "k2"})),
        changed(AUTHORS, lambda d: d["authors"].append(deepcopy(d["authors"][0]))),
        changed(AUTHORS, lambda d: d["authors"][0]["keys"][0].update(valid_from="2019-02-30"))],
    "product": [{**PRODUCT, "public_history_path": "history/another-product"}, {**PRODUCT, "theme_id": "ghost-theme"},
                {**PRODUCT, "author_id": "ghost-author"}],
}


def cases(table):
    return [pytest.param(name, document, id=f"{name}-{index}")
            for name, documents in table.items() for index, document in enumerate(documents)]


@pytest.mark.parametrize("name", NAMES)
def test_schema_is_draft_2020_12_and_says_python_is_authoritative(name):
    document = json.loads((SCHEMAS / f"{name}.schema.json").read_text())
    Draft202012Validator.check_schema(document)
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert document["description"].startswith("Structure only:")
    assert "can still be refused by the engine" in document["description"]
    assert "authoritative" in document["description"]


def test_every_schema_has_fixtures_in_each_category():
    assert sorted(path.name for path in SCHEMAS.iterdir()) == sorted(f"{name}.schema.json" for name in NAMES)
    assert set(VALID) == set(STRUCTURAL) == set(CHECKS) == set(NAMES)
    assert set(RELATIONAL) == set(NAMES) - {"trust"}  # a trust file has no relational rule to express


@pytest.mark.parametrize("name, document", cases(VALID))
def test_documents_python_accepts_are_accepted_by_the_schema(name, document):
    assert accepted(CHECKS[name], document)
    assert schema(name).is_valid(document), list(schema(name).iter_errors(document))


@pytest.mark.parametrize("name, document", cases(STRUCTURAL))
def test_structural_failures_are_rejected_by_both(name, document):
    assert not accepted(CHECKS[name], document)
    assert not schema(name).is_valid(document)


@pytest.mark.parametrize("name, document", cases(RELATIONAL))
def test_relational_and_time_rules_belong_to_the_python_validator(name, document):
    assert schema(name).is_valid(document), list(schema(name).iter_errors(document))
    assert not accepted(CHECKS[name], document)


def test_news_rules_that_need_the_payload_belong_to_python(tmp_path):
    for config in ({**NEWS, "epoch_end": "2020-07-01"}, {**NEWS, "package_id": "other-product"},
                   changed(NEWS, lambda c: c["symbols"].update(DEMOZ={"cik": None, "aliases": ["Zeta"]}))):
        assert schema("news-config").is_valid(config)
        with pytest.raises(Refused):
            newsconfig.validate_news_config(config, NEWS_PAYLOAD)


def test_release_hashes_and_files_belong_to_python(tmp_path):
    root = write_edition(tmp_path / "bundle", KEY, "demo-key", PAYLOAD, evaluation_payload(PAYLOAD))
    release = json.loads((root / "release.json").read_text())
    (root / "REPORT.md").write_text("# Changed after signing\n")
    assert schema("release").is_valid(release)
    with pytest.raises(Refused, match="Release file changed"):
        bundles.verify_bundle(root, TRUST, NOW)


def test_fingerprints_belong_to_python(tmp_path):
    authors = changed(AUTHORS, lambda d: d["authors"][0]["keys"][0].update(fingerprint_sha256="0" * 64))
    assert schema("authors").is_valid(authors)
    themes, _, product = catalog_documents(KEY)
    write(tmp_path / "catalog" / "themes.json", themes)
    write(tmp_path / "catalog" / "authors.json", authors)
    write(tmp_path / "catalog" / "products" / "demo-product.json", product)
    with pytest.raises(Refused, match="Fingerprint mismatch"):
        catalog.check_static(tmp_path)


@pytest.mark.parametrize("name, template", [("snapshot-payload", "payload.template.json"),
                                            ("news-config", "news-config.template.json")])
def test_author_kit_templates_match_their_schemas(name, template):
    assert schema(name).is_valid(json.loads((ROOT / "author-kit" / template).read_text()))


def test_evaluation_template_matches_the_payload_part_of_its_schema():
    payload = json.loads((ROOT / "author-kit" / "evaluation.template.json").read_text())
    document = {"format": "public-pilot-evaluation-v1", "key_id": "example-author-2020", "payload": payload,
                "signature": "A" * 86 + "=="}
    assert schema("evaluation").is_valid(document)


def test_a_key_without_products_needs_a_theme_listing_its_author_which_only_python_checks(tmp_path):
    authors = changed(AUTHORS, lambda d: d["authors"][0]["keys"][0].update(packages=[]))
    assert schema("authors").is_valid(authors) and accepted(catalog.validate_authors, authors)
    themes = changed(THEMES, lambda d: d["themes"][0].update(author_ids=[], product_ids=[],
                                                              latest_public_quarter=None))
    write(tmp_path / "catalog" / "themes.json", themes)
    write(tmp_path / "catalog" / "authors.json", authors)
    (tmp_path / "catalog" / "products").mkdir()
    with pytest.raises(Refused, match="^Key demo-key lists no products, which is allowed only while a theme lists "
                                      "author demo-author$"):
        catalog.check_static(tmp_path)
    write(tmp_path / "catalog" / "themes.json", changed(themes, lambda d: d["themes"][0].update(
        author_ids=["demo-author"])))
    assert catalog.check_static(tmp_path)[1]["demo-author"]["keys"][0]["packages"] == []
