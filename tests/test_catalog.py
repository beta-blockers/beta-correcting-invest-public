"""Catalog checks, trust files, the history index and the append-only rule for authors.json."""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil

import pytest

from public_pilot import authoring, catalog
from public_pilot.bundles import verify_bundle
from public_pilot.common import Refused, digest, now
from support import (NOW, build_repository, call, catalog_documents, edition_payload, evaluation_payload, new_key,
                     read, write, write_edition)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def signer(tmp_path):
    directory = tmp_path / "keys"
    directory.mkdir(mode=0o700)
    return new_key(directory)[0]


@pytest.fixture
def repo(tmp_path, signer):
    return build_repository(tmp_path / "repo", signer)


def edit(path, change):
    document = read(path)
    change(document)
    write(path, document)


def test_the_repository_catalog_passes():
    result = catalog.check(ROOT, now())
    assert result["status"] == "verified"
    # Real authors, products and unexpired demo editions may be added to the public catalog.
    assert result["themes"] == len(read(ROOT / "catalog" / "themes.json")["themes"])
    assert result["authors"] == len(read(ROOT / "catalog" / "authors.json")["authors"])
    assert result["products"] == len(list((ROOT / "catalog" / "products").glob("*.json")))


def test_fictional_repository_passes_and_reports_expired(repo, capsys):
    code, output = call(capsys, ["catalog", "check", repo])
    assert code == 0 and output["editions"] == [{"product_id": "demo-product", "quarter": "2020-Q1",
                                                 "edition_id": "demo-product-2020-q1", "expired": True}]
    assert (output["themes"], output["authors"], output["products"]) == (1, 1, 1)


def theme(change):
    return lambda document: change(document["themes"][0])


def key(change):
    return lambda document: change(document["authors"][0]["keys"][0])


BROKEN_REFERENCES = [
    ("themes.json", theme(lambda t: t["author_ids"].append("ghost-author")), "Theme demo-theme lists unknown author ghost-author"),
    ("themes.json", theme(lambda t: t["product_ids"].append("ghost-product")), "Theme demo-theme lists unknown product ghost-product"),
    ("themes.json", theme(lambda t: t["product_ids"].clear()), "Theme demo-theme does not list product demo-product"),
    ("themes.json", theme(lambda t: t["author_ids"].clear()), "Theme demo-theme does not list author demo-author of product demo-product"),
    ("themes.json", theme(lambda t: t.update(latest_public_quarter="2019-Q4")), "Theme demo-theme: latest_public_quarter must be 2020-Q1"),
    ("products/demo-product.json", lambda p: p.update(theme_id="ghost-theme"), "Product demo-product names unknown theme ghost-theme"),
    ("products/demo-product.json", lambda p: p.update(author_id="ghost-author"), "Product demo-product names unknown author ghost-author"),
    ("products/demo-product.json", lambda p: p.update(public_history_path="history/elsewhere"), "Product demo-product must keep its public history in history/demo-product"),
    ("authors.json", key(lambda k: k["packages"].append("ghost-product")), "Key demo-key lists ghost-product, which is not a product of author demo-author"),
]


@pytest.mark.parametrize("name, change, message", BROKEN_REFERENCES)
def test_each_broken_reference_fails_with_a_specific_message(repo, name, change, message):
    edit(repo / "catalog" / name, change)
    with pytest.raises(Refused, match="^" + re.escape(message) + "$"):
        catalog.check(repo, NOW)


def test_history_without_a_product_and_misnamed_product_files_fail(repo):
    shutil.copytree(repo / "history" / "demo-product", repo / "history" / "orphan-product")
    with pytest.raises(Refused, match="^history/orphan-product/2020-Q1 has no product entry in catalog/products$"):
        catalog.check(repo, NOW)
    shutil.rmtree(repo / "history" / "orphan-product")
    (repo / "catalog" / "products" / "demo-product.json").rename(repo / "catalog" / "products" / "renamed.json")
    with pytest.raises(Refused, match="must be named after its product_id"):
        catalog.check(repo, NOW)


def test_fingerprint_mismatch_fails_with_a_specific_message(repo):
    edit(repo / "catalog" / "authors.json", key(lambda k: k.update(fingerprint_sha256="0" * 64)))
    with pytest.raises(Refused, match="^Fingerprint mismatch for key demo-key$"):
        catalog.check(repo, NOW)


@pytest.mark.parametrize("change, message", [
    ({"status": "revoked"}, "edition.snapshot.json is signed by key demo-key, which the catalog does not list as a "
                            "key of author demo-author for package demo-product that is not revoked"),
    ({"key_id": "renamed-key"}, "edition.snapshot.json is signed by key demo-key, which the catalog does not list"),
    ({"valid_from": "2020-01-03"}, "^history/demo-product/2020-Q1 was published on 2020-01-02, before author "
                                   "demo-author had a catalog key for demo-product$"),
])
def test_editions_need_a_key_of_that_author_and_package_listed_by_the_publication_date(tmp_path, signer, change,
                                                                                       message):
    repo = build_repository(tmp_path / "repo", signer)
    edit(repo / "catalog" / "authors.json", key(lambda k: k.update(change)))
    with pytest.raises(Refused, match=message):
        catalog.check(repo, NOW)


def test_unknown_key_fails_with_a_specific_message(tmp_path, signer):
    stranger, _ = new_key(tmp_path / "keys", "stranger.key")
    repo = build_repository(tmp_path / "repo", signer)
    edition = repo / "history" / "demo-product" / "2020-Q1"
    for name in ("edition.snapshot.json", "evaluation.json", "release.json", "REPORT.md", "account.fixture.json"):
        (edition / name).unlink()
    edition.rmdir()
    payload = edition_payload()
    write_edition(edition, stranger, "stranger-key", payload, evaluation_payload(payload))
    with pytest.raises(Refused, match="signed by key stranger-key, which the catalog does not list as a key of"):
        catalog.check(repo, NOW)


@pytest.mark.parametrize("evaluation_changes, message", [
    ({"package_sha256": digest({**edition_payload(), "research": "Another edition."})}, "package_sha256 mismatch"),
    ({"companies": None}, "weight for DEMOA differs from the payload target"),
])
def test_bundle_can_pass_while_the_evaluation_fails_catalog_check(tmp_path, signer, evaluation_changes, message):
    payload = edition_payload()
    changes = dict(evaluation_changes)
    if changes.get("companies", 0) is None:
        companies = deepcopy(evaluation_payload(payload)["companies"])
        companies["DEMOA"]["weight"] = "0.4"
        changes["companies"] = companies
    repo = build_repository(tmp_path / "repo", signer, evaluation_changes=changes)
    edition = repo / "history" / "demo-product" / "2020-Q1"
    trust = catalog.product_trust(repo, "demo-product")
    assert verify_bundle(edition, trust, NOW)["status"] == "verified"
    with pytest.raises(Refused, match=re.escape(message)):
        catalog.check(repo, NOW)


@pytest.mark.parametrize("damage", ["extra", "missing"])
def test_history_directories_hold_exactly_five_files(repo, damage):
    edition = repo / "history" / "demo-product" / "2020-Q1"
    if damage == "extra":
        (edition / "notes.txt").write_text("stray")
    else:
        (edition / "REPORT.md").unlink()
    with pytest.raises(Refused, match="must hold exactly: REPORT.md, account.fixture.json"):
        catalog.check(repo, NOW)


def test_history_editions_must_not_be_tradable_paper_editions(tmp_path, signer):
    repo = build_repository(tmp_path / "repo", signer)
    edition = repo / "history" / "demo-product" / "2021-Q1"
    payload = {**edition_payload(), "purpose": "paper", "edition_id": "paper-edition"}
    write_edition(edition, signer, "demo-key", payload, evaluation_payload(payload))
    edit(repo / "catalog" / "themes.json", theme(lambda t: t.update(latest_public_quarter="2021-Q1")))
    with pytest.raises(Refused, match="trusted only for demonstrations"):
        catalog.check(repo, NOW)


@pytest.mark.parametrize("name, change, message", [
    ("themes.json", theme(lambda t: t.update(status="planned")), "Theme status"),
    ("themes.json", theme(lambda t: t.update(committed_on="2019-02-30")), "committed_on"),
    ("themes.json", lambda d: d["themes"].append(deepcopy(d["themes"][0])), "Duplicate theme ID"),
    ("authors.json", key(lambda k: k.update(status="lost")), "Key status"),
    ("authors.json", key(lambda k: k.update(public_key="not-a-key")), "Invalid public key"),
    ("products/demo-product.json", lambda p: p.update(review_status="reviewed"), "author_published"),
    ("products/demo-product.json", lambda p: p.update(universe_size=0), "universe_size"),
    ("products/demo-product.json", lambda p: p.update(cadence="monthly"), "quarterly"),
    ("products/demo-product.json", lambda p: p.update(extra="field"), "unknown document fields"),
])
def test_catalog_structure_is_validated(repo, name, change, message):
    edit(repo / "catalog" / name, change)
    with pytest.raises(Refused, match=message):
        catalog.check(repo, NOW)


def test_stray_files_in_catalog_and_history_are_refused(repo):
    (repo / "catalog" / "notes.md").write_text("stray")
    with pytest.raises(Refused, match="catalog/ holds exactly"):
        catalog.check(repo, NOW)
    (repo / "catalog" / "notes.md").unlink()
    (repo / "history" / "README.md").write_text("stray")
    with pytest.raises(Refused, match="Unexpected entry in history/: README.md"):
        catalog.check(repo, NOW)


def test_trust_file_from_the_catalog(repo, signer, tmp_path, capsys):
    code, output = call(capsys, ["catalog", "trust", repo, "--product", "demo-product", "--out", tmp_path / "t.json"])
    assert code == 0 and output["allow_paper"] is False and output["keys"] == ["demo-key"]
    assert read(tmp_path / "t.json") == {"demo-key": {"public_key": authoring.public_key(signer),
                                                      "author_id": "demo-author", "packages": ["demo-product"],
                                                      "allow_paper": False}}
    assert call(capsys, ["catalog", "trust", repo, "--product", "demo-product", "--out", tmp_path / "t.json"])[0] == 2
    code, output = call(capsys, ["catalog", "trust", repo, "--product", "demo-product", "--out",
                                 tmp_path / "paper.json", "--allow-paper"])
    assert code == 0 and read(tmp_path / "paper.json")["demo-key"]["allow_paper"] is True
    code, output = call(capsys, ["--trust", tmp_path / "t.json", "verify-bundle",
                                 repo / "history" / "demo-product" / "2020-Q1"])
    assert code == 0 and output["expired"] is True
    assert call(capsys, ["catalog", "trust", repo, "--product", "ghost", "--out", tmp_path / "g.json"])[0] == 2


def test_trust_files_leave_out_revoked_keys_and_never_let_retired_keys_trade(repo, tmp_path):
    second, _ = new_key(tmp_path / "keys", "second.key")
    third, _ = new_key(tmp_path / "keys", "third.key")

    def add_keys(document):
        for private, key_id, status in ((second, "retired-key", "retired"), (third, "revoked-key", "revoked")):
            public = authoring.public_key(private)
            document["authors"][0]["keys"].append({
                "key_id": key_id, "public_key": public, "fingerprint_sha256": authoring.fingerprint(public),
                "status": status, "valid_from": "2019-06-01", "packages": ["demo-product"]})

    edit(repo / "catalog" / "authors.json", add_keys)
    trust = catalog.product_trust(repo, "demo-product", allow_paper=True)
    assert sorted(trust) == ["demo-key", "retired-key"]
    assert trust["demo-key"]["allow_paper"] is True and trust["retired-key"]["allow_paper"] is False


def test_history_index_is_generated_and_checked(repo, capsys):
    code, refusal = call(capsys, ["history", "index", repo, "--check"])
    assert code == 2 and "out of date" in refusal["reason"]
    code, output = call(capsys, ["history", "index", repo])
    listed = [{"product_id": "demo-product", "quarter": "2020-Q1", "edition_id": "demo-product-2020-q1",
               "expired": True}]
    assert code == 0 and output == {"status": "written", "path": "history/INDEX.md", "editions": listed}
    index = (repo / "history" / "INDEX.md").read_text()
    assert ("| demo-product | 2020-Q1 | demo-product-2020-q1 | 2019-12-31T00:00:00+00:00 | "
            "2020-04-01T00:00:00+00:00 | 3 | yes |") in index.splitlines()
    assert call(capsys, ["history", "index", repo, "--check"]) == (0, {"status": "current",
                                                                      "path": "history/INDEX.md", "editions": listed})
    assert catalog.check(repo, NOW)["status"] == "verified"
    (repo / "history" / "INDEX.md").write_text(index.replace("| yes |", "| no |"))
    assert call(capsys, ["history", "index", repo, "--check"])[0] == 2


def test_repository_history_index_is_current(capsys):
    assert call(capsys, ["history", "index", ROOT, "--check"])[0] == 0


# authors.json is append-only -----------------------------------------------------------

def appended(signer, tmp_path):
    base = catalog_documents(signer)[1]
    other, _ = new_key(tmp_path / "keys", "other.key")
    public = authoring.public_key(other)
    new_key_entry = {"key_id": "demo-key-2", "public_key": public, "fingerprint_sha256": authoring.fingerprint(public),
                     "status": "active", "valid_from": "2021-01-01", "packages": ["demo-product"]}
    return base, new_key_entry


def test_appending_authors_keys_and_packages_and_changing_status_is_allowed(signer, tmp_path):
    base, new_entry = appended(signer, tmp_path)
    grown = deepcopy(base)
    grown["authors"][0]["keys"][0]["status"] = "retired"
    grown["authors"][0]["keys"][0]["packages"].append("demo-product-2")
    grown["authors"][0]["keys"].append(new_entry)
    third, _ = new_key(tmp_path / "keys", "third.key")
    public = authoring.public_key(third)
    grown["authors"].append({"author_id": "new-author", "display_name": "Another fictional author", "keys": [
        {**new_entry, "key_id": "new-key", "public_key": public, "fingerprint_sha256": authoring.fingerprint(public),
         "packages": ["new-product"]}]})
    assert catalog.check_append_only(base, grown) is True


@pytest.mark.parametrize("change, message", [
    (lambda d, _: d["authors"].clear(), "an author was removed"),
    (lambda d, _: d["authors"][0].update(author_id="renamed"), "removed, renamed or moved"),
    (lambda d, _: d["authors"][0].update(display_name="Renamed"), "display name"),
    (lambda d, _: d["authors"][0]["keys"].pop(), "a key of demo-author was removed"),
    (lambda d, _: d["authors"][0]["keys"].reverse(), "key demo-key was edited"),
    (lambda d, _: d["authors"][0]["keys"][0].update(valid_from="2018-01-01"), "key demo-key was edited"),
    (lambda d, fresh: d["authors"][0]["keys"][0].update(public_key=fresh), "key demo-key was edited"),
    (lambda d, _: d["authors"][0]["keys"][0].update(packages=["other-product"]), "package of key demo-key"),
])
def test_deleting_or_editing_authors_is_refused(signer, tmp_path, change, message):
    base, second = appended(signer, tmp_path)
    base["authors"][0]["keys"].append(second)
    edited = deepcopy(base)
    change(edited, authoring.public_key(new_key(tmp_path / "keys", "fresh.key")[0]))
    with pytest.raises(Refused, match=message):
        catalog.check_append_only(base, edited)


def test_append_only_rule_runs_from_catalog_check(repo, tmp_path, capsys):
    base = tmp_path / "base"
    shutil.copytree(repo, base)
    code, output = call(capsys, ["catalog", "check", repo, "--base", base])
    assert code == 0 and output["append_only"] is True
    edit(repo / "catalog" / "authors.json", lambda d: d["authors"][0].update(display_name="Renamed"))
    code, refusal = call(capsys, ["catalog", "check", repo, "--base", base])
    assert code == 2 and "append-only" in refusal["reason"]
    write(base / "catalog" / "authors.json", {"format": "public-pilot-authors-v1", "authors": "none"})
    code, refusal = call(capsys, ["catalog", "check", repo, "--base", base])
    assert code == 2 and "base catalog/authors.json is invalid" in refusal["reason"]
    code, refusal = call(capsys, ["catalog", "check", repo, "--base", tmp_path / "missing"])
    assert code == 2 and refusal["reason"] == "Base directory not found"


def test_trust_validator_matches_engine_grants():
    good = {"k": {"public_key": "A" * 43 + "=", "author_id": "a", "packages": ["p"], "allow_paper": False}}
    assert catalog.validate_trust(good) == good
    for broken in ({"k": {**good["k"], "allow_paper": "no"}}, {"k": {**good["k"], "packages": "p"}},
                   {"k": {**good["k"], "extra": 1}}, {"k": {**good["k"], "public_key": "short"}}, []):
        with pytest.raises(Refused):
            catalog.validate_trust(broken)
    assert json.loads(json.dumps(good)) == good


def test_public_keys_must_use_the_canonical_encoding(repo):
    def noncanonical(document):
        key = document["authors"][0]["keys"][0]
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        key["public_key"] = key["public_key"][:42] + alphabet[alphabet.index(key["public_key"][42]) | 1] + "="

    edit(repo / "catalog" / "authors.json", noncanonical)
    with pytest.raises(Refused, match="canonical standard base64"):
        catalog.check(repo, NOW)


def test_a_revoked_key_cannot_be_listed_again_under_another_id(repo, tmp_path):
    base = read(repo / "catalog" / "authors.json")
    base["authors"][0]["keys"][0]["status"] = "revoked"
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    for spelling in ("same", "noncanonical"):
        relisted = deepcopy(base)
        key = deepcopy(relisted["authors"][0]["keys"][0])
        if spelling == "noncanonical":
            key["public_key"] = key["public_key"][:42] + alphabet[alphabet.index(key["public_key"][42]) | 1] + "="
        relisted["authors"][0]["keys"].append({**key, "key_id": "demo-key-again", "status": "active"})
        with pytest.raises(Refused, match="listed twice|canonical"):
            catalog.check_append_only(base, relisted)


def test_a_theme_cannot_list_another_themes_product(repo):
    def second_theme(document):
        other = deepcopy(document["themes"][0])
        other.update(theme_id="other-theme", latest_public_quarter=None)
        document["themes"].append(other)

    edit(repo / "catalog" / "themes.json", second_theme)
    with pytest.raises(Refused, match="^Theme other-theme lists product demo-product, which belongs to theme demo-theme$"):
        catalog.check(repo, NOW)


def test_an_edition_id_appears_once_in_a_products_history(repo):
    shutil.copytree(repo / "history" / "demo-product" / "2020-Q1", repo / "history" / "demo-product" / "2020-Q2")
    edit(repo / "catalog" / "themes.json", theme(lambda t: t.update(latest_public_quarter="2020-Q2")))
    with pytest.raises(Refused, match="edition demo-product-2020-q1 appears in both 2020-Q1 and 2020-Q2"):
        catalog.check(repo, NOW)


# Key replacement: re-signing past editions, and history/ relative to its base -------------------

EDITION = Path("history") / "demo-product" / "2020-Q1"


def replace_key(repo, keys, status="revoked", valid_from="2026-01-15"):
    """Mark demo-key revoked (or retired) and append a replacement key listed long after the 2020 edition."""
    private, created = new_key(keys, "replacement.key")

    def change(document):
        document["authors"][0]["keys"][0]["status"] = status
        document["authors"][0]["keys"].append({
            "key_id": "demo-key-2", "public_key": created["public_key"],
            "fingerprint_sha256": created["fingerprint_sha256"], "status": "active", "valid_from": valid_from,
            "packages": ["demo-product"]})

    edit(repo / "catalog" / "authors.json", change)
    return private, created["key"]


def resign(capsys, repo, key_file, scratch, key_id="demo-key-2"):
    code, output = call(capsys, ["resign-edition", repo / EDITION, scratch / "resigned", "--key", key_file,
                                 "--key-id", key_id])
    assert code == 0, output
    shutil.rmtree(repo / EDITION)
    (scratch / "resigned").rename(repo / EDITION)
    return output


@pytest.mark.parametrize("status", ["revoked", "retired"])
def test_a_replacement_key_re_signs_past_editions_and_the_catalog_accepts_them(repo, tmp_path, capsys, monkeypatch,
                                                                               status):
    monkeypatch.setattr("public_pilot.cli.now", lambda: NOW)
    catalog.history_index(repo, NOW)
    base = tmp_path / "base"
    shutil.copytree(repo, base)
    payload_hash = digest(read(repo / EDITION / "edition.snapshot.json")["payload"])
    _, key_file = replace_key(repo, tmp_path / "keys", status)
    if status == "revoked":
        with pytest.raises(Refused, match="signed by key demo-key, which the catalog does not list"):
            catalog.check(repo, NOW)
    output = resign(capsys, repo, key_file, tmp_path)
    assert (output["status"], output["sha256"], output["key_id"]) == ("re-signed", payload_hash, "demo-key-2")
    for name in ("edition.snapshot.json", "evaluation.json", "release.json"):
        assert read(repo / EDITION / name)["key_id"] == "demo-key-2"
    for name in ("REPORT.md", "account.fixture.json"):
        assert (repo / EDITION / name).read_bytes() == (base / EDITION / name).read_bytes()
    assert catalog.check(repo, NOW, base)["append_only"] is True
    assert catalog.history_index(repo, NOW, check_only=True)["status"] == "current"
    trust = catalog.product_trust(repo, "demo-product")
    assert ("demo-key" in trust) == (status == "retired") and "demo-key-2" in trust
    assert verify_bundle(repo / EDITION, trust, NOW)["status"] == "verified"


def test_a_new_author_key_cannot_verify_editions_from_before_the_author_was_listed(repo, tmp_path, capsys,
                                                                                    monkeypatch):
    monkeypatch.setattr("public_pilot.cli.now", lambda: NOW)
    _, key_file = replace_key(repo, tmp_path / "keys")
    edit(repo / "catalog" / "authors.json", key(lambda k: k.update(valid_from="2020-06-01")))
    resign(capsys, repo, key_file, tmp_path)
    with pytest.raises(Refused, match="was published on 2020-01-02, before author demo-author had a catalog key"):
        catalog.check(repo, NOW)


def test_resign_edition_refuses_to_overwrite_or_to_copy_a_changed_edition(repo, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("public_pilot.cli.now", lambda: NOW)
    _, key_file = replace_key(repo, tmp_path / "keys")
    argv = ["resign-edition", repo / EDITION, tmp_path / "copy", "--key", key_file, "--key-id", "demo-key-2"]
    (tmp_path / "copy").mkdir()
    code, refusal = call(capsys, argv)
    assert code == 2 and "already exists" in refusal["reason"]
    (tmp_path / "copy").rmdir()
    report = repo / EDITION / "REPORT.md"
    report.write_text(report.read_text() + "Edited after release.\n")
    code, refusal = call(capsys, argv)
    assert code == 2 and "no longer match its release.json" in refusal["reason"]
    assert not (tmp_path / "copy").exists()
    report.unlink()
    code, refusal = call(capsys, argv)
    assert code == 2 and "must hold exactly" in refusal["reason"]


def test_resign_edition_refuses_paper_editions(tmp_path, signer, capsys, monkeypatch):
    monkeypatch.setattr("public_pilot.cli.now", lambda: NOW)
    repo = build_repository(tmp_path / "repo", signer)
    paper = repo / "history" / "demo-product" / "2021-Q1"
    payload = {**edition_payload(), "purpose": "paper", "edition_id": "paper-edition"}
    write_edition(paper, signer, "demo-key", payload, evaluation_payload(payload))
    _, key_file = replace_key(repo, tmp_path / "keys")
    code, refusal = call(capsys, ["resign-edition", paper, tmp_path / "copy", "--key", key_file,
                                  "--key-id", "demo-key-2"])
    assert code == 2 and refusal["reason"] == "Only demo editions, as under history/, are re-signed this way"


@pytest.mark.parametrize("damage, message", [
    ("remove", "history/demo-product/2020-Q1 was removed; only an edition whose signatures are all by revoked "
               "keys may be removed"),
    ("report", "history/demo-product/2020-Q1 changed; an existing edition may only be re-signed"),
    ("payload", "history/demo-product/2020-Q1 changed; an existing edition may only be re-signed"),
])
def test_history_only_appends_to_its_base(repo, signer, tmp_path, damage, message):
    base = tmp_path / "base"
    shutil.copytree(repo, base)
    if damage == "remove":
        shutil.copytree(repo / EDITION, repo / "history" / "demo-product" / "2020-Q2")
        shutil.rmtree(repo / EDITION)
        edit(repo / "catalog" / "themes.json", theme(lambda t: t.update(latest_public_quarter="2020-Q2")))
    elif damage == "report":
        shutil.rmtree(repo / EDITION)
        payload = edition_payload()
        write_edition(repo / EDITION, signer, "demo-key", payload, evaluation_payload(payload))
        (repo / EDITION / "release.json").unlink()
        (repo / EDITION / "REPORT.md").write_text("A different report.\n")
        authoring.write_new(repo / EDITION / "release.json",
                            authoring.sign_release(signer, "demo-key", repo / EDITION, "edition.snapshot.json", NOW))
    else:
        shutil.rmtree(repo / EDITION)
        payload = {**edition_payload(), "targets": {"DEMOA": "0.5", "DEMOB": "0.3"}}
        write_edition(repo / EDITION, signer, "demo-key", payload, evaluation_payload(payload))
    assert catalog.check(repo, NOW)["status"] == "verified"  # each change is consistent and correctly signed
    with pytest.raises(Refused, match="^history/ is append-only: " + re.escape(message)):
        catalog.check(repo, NOW, base)


def test_an_edition_published_before_a_key_change_can_be_added_with_the_new_key(repo, tmp_path):
    """An edition sold before the key change and added to the public history later: the new key signs it."""
    base = tmp_path / "base"
    shutil.copytree(repo, base)
    later_key, _ = replace_key(repo, tmp_path / "keys")
    edition = repo / "history" / "demo-product" / "2020-Q2"
    payload = {**edition_payload(), "edition_id": "demo-product-2020-q2"}
    write_edition(edition, later_key, "demo-key-2", payload, evaluation_payload(payload))
    shutil.rmtree(repo / EDITION)
    write_edition(repo / EDITION, later_key, "demo-key-2", edition_payload(), evaluation_payload(edition_payload()))
    edit(repo / "catalog" / "themes.json", theme(lambda t: t.update(latest_public_quarter="2020-Q2")))
    assert catalog.check(repo, NOW, base)["append_only"] is True


@pytest.mark.parametrize("status", ["revoked", "retired"])
def test_only_an_edition_signed_with_revoked_keys_may_be_withdrawn(repo, tmp_path, status):
    """An edition forged with an exposed key is withdrawn by revoking the key and removing its directory."""
    base = tmp_path / "base"
    shutil.copytree(repo, base)
    replace_key(repo, tmp_path / "keys", status)
    shutil.rmtree(repo / EDITION)
    edit(repo / "catalog" / "themes.json", theme(lambda t: t.update(latest_public_quarter=None)))
    if status == "revoked":
        assert catalog.check(repo, NOW, base)["append_only"] is True
    else:
        with pytest.raises(Refused, match="2020-Q1 was removed; only an edition whose signatures are all by revoked"):
            catalog.check(repo, NOW, base)


# A genuinely new author: registered with a theme before any product ----------------------------------------------

NEW_THEME = {"theme_id": "new-theme", "title": "Fictional new theme", "geographies": ["SYNTHETIC"],
             "policy_ids": ["fictional-policy"], "status": "committed", "author_ids": ["new-author"], "product_ids": [],
             "committed_on": "2019-06-01", "latest_public_quarter": None}
NEW_PRODUCT = {"format": "public-pilot-product-v1", "product_id": "new-product", "theme_id": "new-theme",
               "author_id": "new-author", "cadence": "quarterly", "universe_size": 3,
               "methodology_summary": "Fictional first product of a new author.",
               "public_history_path": "history/new-product", "review_status": "author_published"}


def register(repo, keys, capsys, packages=(), theme=True):
    """CONTRIBUTING.md's first pull request through the command line: keygen outside every checkout, then the author
    entry with its public key and a committed theme without products. Returns the new private key."""
    code, created = call(capsys, ["keygen", "--out", keys / "new-author.key"])
    assert code == 0
    edit(repo / "catalog" / "authors.json", lambda d: d["authors"].append({
        "author_id": "new-author", "display_name": "New Author (fictional)", "keys": [{
            "key_id": "new-key", "public_key": created["public_key"],
            "fingerprint_sha256": created["fingerprint_sha256"], "status": "active", "valid_from": "2019-06-01",
            "packages": list(packages)}]}))
    if theme:
        edit(repo / "catalog" / "themes.json", lambda d: d["themes"].append(deepcopy(NEW_THEME)))
    return authoring.load_private_key(created["key"])


def publish_first_product(repo):
    """The later pull request: the product entry, listed by the theme and appended to the key's packages."""
    write(repo / "catalog" / "products" / "new-product.json", NEW_PRODUCT)
    edit(repo / "catalog" / "themes.json", lambda d: d["themes"][-1].update(
        product_ids=["new-product"], status="in_progress"))
    edit(repo / "catalog" / "authors.json", lambda d: d["authors"][-1]["keys"][0]["packages"].append("new-product"))


@pytest.fixture
def keys(tmp_path):
    directory = tmp_path / "new-keys"
    directory.mkdir(mode=0o700)
    return directory


def test_a_new_author_registers_with_a_theme_before_any_product(repo, tmp_path, keys, capsys):
    base = tmp_path / "base"
    shutil.copytree(repo, base)
    register(repo, keys, capsys)
    code, output = call(capsys, ["catalog", "check", repo, "--base", base])
    assert code == 0 and output["append_only"] is True
    assert (output["themes"], output["authors"], output["keys"], output["products"]) == (2, 2, 2, 1)
    assert call(capsys, ["history", "index", repo])[0] == 0
    assert call(capsys, ["history", "index", repo, "--check"])[0] == 0


@pytest.mark.parametrize("themes, listed", [
    pytest.param(lambda d: None, False, id="no theme"),
    pytest.param(lambda d: d["themes"].append(deepcopy(NEW_THEME)), True, id="own theme"),
    pytest.param(lambda d: d["themes"][0]["author_ids"].append("new-author"), True, id="existing theme"),
])
def test_a_key_without_products_is_accepted_only_while_a_theme_lists_its_author(repo, keys, capsys, themes, listed):
    register(repo, keys, capsys, theme=False)
    edit(repo / "catalog" / "themes.json", themes)
    code, output = call(capsys, ["catalog", "check", repo])
    if listed:
        assert code == 0 and output["status"] == "verified"
    else:
        assert code == 2 and output["reason"] == ("Key new-key lists no products, which is allowed only while a "
                                                  "theme lists author new-author")


def test_a_key_without_products_grants_no_signing_or_trading_authority(repo, tmp_path, keys, capsys):
    private = register(repo, keys, capsys)
    # No trust file names the planned product, and other products' trust files leave the key out.
    code, refusal = call(capsys, ["catalog", "trust", repo, "--product", "new-product", "--out", tmp_path / "n.json"])
    assert code == 2 and refusal["reason"] == "Unknown product new-product" and not (tmp_path / "n.json").exists()
    code, output = call(capsys, ["catalog", "trust", repo, "--product", "demo-product", "--allow-paper", "--out",
                                 tmp_path / "demo.json"])
    assert code == 0 and output["keys"] == ["demo-key"] and "new-key" not in read(tmp_path / "demo.json")
    # Nothing the key signs verifies with trust built from the catalog.
    payload = edition_payload()
    signed = write_edition(tmp_path / "signed-by-new-key", private, "new-key", payload, evaluation_payload(payload))
    code, refusal = call(capsys, ["--trust", tmp_path / "demo.json", "verify-bundle", signed])
    assert code == 2 and refusal["reason"] == "Publisher is not in the local trust store"
    # And it cannot sign a history edition, not even one claiming to be by the new author.
    edit(repo / "catalog" / "themes.json", lambda d: d["themes"][0].update(latest_public_quarter="2020-Q2"))
    for author in ("demo-author", "new-author"):
        target = repo / "history" / "demo-product" / "2020-Q2"
        shutil.rmtree(target, ignore_errors=True)
        forged = {**edition_payload(author=author), "edition_id": "demo-product-2020-q2"}
        write_edition(target, private, "new-key", forged, evaluation_payload(forged))
        code, refusal = call(capsys, ["catalog", "check", repo])
        assert code == 2 and refusal["reason"] == (
            "history/demo-product/2020-Q2/edition.snapshot.json is signed by key new-key, which the catalog does not "
            "list as a key of author demo-author for package demo-product that is not revoked")


@pytest.mark.parametrize("packages, message", [
    pytest.param(["new-product"], "Key new-key lists new-product, which is not a product of author new-author",
                 id="planned product"),
    pytest.param(["demo-product"], "Key new-key lists demo-product, which is not a product of author new-author",
                 id="another author's product"),
])
def test_a_new_key_may_not_name_a_planned_or_another_authors_product(repo, tmp_path, keys, capsys, packages, message):
    register(repo, keys, capsys, packages=packages)
    for command in (["catalog", "check", repo], ["catalog", "trust", repo, "--product", "demo-product", "--out",
                                                  tmp_path / "t.json"]):
        code, refusal = call(capsys, command)
        assert code == 2 and refusal["reason"] == message


def test_the_first_product_grants_authority_for_that_product_only(repo, tmp_path, keys, capsys):
    private = register(repo, keys, capsys)
    registered = tmp_path / "registered"
    shutil.copytree(repo, registered)
    # The product alone grants nothing: the key does not list it yet.
    write(repo / "catalog" / "products" / "new-product.json", NEW_PRODUCT)
    edit(repo / "catalog" / "themes.json", lambda d: d["themes"][-1].update(product_ids=["new-product"]))
    assert call(capsys, ["catalog", "check", repo])[0] == 0
    code, refusal = call(capsys, ["catalog", "trust", repo, "--product", "new-product", "--out", tmp_path / "t.json"])
    assert code == 2 and refusal["reason"] == "The catalog lists no valid key for product new-product"
    # Appending the product to the key is allowed by the append-only rule and grants authority for it alone.
    shutil.rmtree(repo)
    shutil.copytree(registered, repo)
    publish_first_product(repo)
    code, output = call(capsys, ["catalog", "check", repo, "--base", registered])
    assert code == 0 and output["append_only"] is True and output["products"] == 2
    code, output = call(capsys, ["catalog", "trust", repo, "--product", "new-product", "--allow-paper", "--out",
                                 tmp_path / "new.json"])
    assert code == 0 and output["keys"] == ["new-key"] and output["allow_paper"] is True
    assert call(capsys, ["catalog", "trust", repo, "--product", "demo-product", "--out", tmp_path / "demo.json"])[1][
        "keys"] == ["demo-key"]
    # Its first edition: signed by the new key, accepted by the catalog and listed in the history index.
    payload = edition_payload(product="new-product", author="new-author")
    write_edition(repo / "history" / "new-product" / "2020-Q1", private, "new-key", payload,
                  evaluation_payload(payload))
    edit(repo / "catalog" / "themes.json", lambda d: d["themes"][-1].update(latest_public_quarter="2020-Q1",
                                                                             status="researched"))
    assert call(capsys, ["history", "index", repo])[0] == 0
    code, output = call(capsys, ["catalog", "check", repo, "--base", registered])
    assert code == 0 and ("new-product", "2020-Q1") in {(e["product_id"], e["quarter"]) for e in output["editions"]}
    assert call(capsys, ["history", "index", repo, "--check"])[0] == 0
    code, output = call(capsys, ["--trust", tmp_path / "new.json", "verify-bundle",
                                 repo / "history" / "new-product" / "2020-Q1"])
    assert code == 0 and output["edition_id"] == "new-product-2020-q1"


def test_after_the_first_product_the_key_still_cannot_take_another_authors_product(repo, tmp_path, keys, capsys):
    register(repo, keys, capsys)
    publish_first_product(repo)
    base = tmp_path / "base"
    shutil.copytree(repo, base)
    # Appending is allowed by the append-only rule, but ownership is still checked.
    edit(repo / "catalog" / "authors.json", lambda d: d["authors"][-1]["keys"][0]["packages"].append("demo-product"))
    code, refusal = call(capsys, ["catalog", "check", repo, "--base", base])
    assert code == 2 and refusal["reason"] == "Key new-key lists demo-product, which is not a product of author new-author"
