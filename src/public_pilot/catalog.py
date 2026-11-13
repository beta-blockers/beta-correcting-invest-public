"""The catalog of themes, authors and products, and checks of the signed public history it indexes."""
from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import re

from . import authoring
from .authoring import fingerprint, write_new
from .bundles import RELEASE_NAME, check_release, file_sha256, inventory, open_member, read_member_json, scan
from .common import Refused, digest, fields, iso, require, timestamp
from .evaluation import verify_evaluation
from .packages import IDENTIFIER, resolve_historical

THEMES_FORMAT = "public-pilot-themes-v1"
AUTHORS_FORMAT = "public-pilot-authors-v1"
PRODUCT_FORMAT = "public-pilot-product-v1"
THEME_FIELDS = ("theme_id", "title", "geographies", "policy_ids", "status", "author_ids", "product_ids",
                "committed_on", "latest_public_quarter")
AUTHOR_FIELDS = ("author_id", "display_name", "keys")
KEY_FIELDS = ("key_id", "public_key", "fingerprint_sha256", "status", "valid_from", "packages")
PRODUCT_FIELDS = ("format", "product_id", "theme_id", "author_id", "cadence", "universe_size",
                  "methodology_summary", "public_history_path", "review_status")
THEME_STATUSES = ("researched", "in_progress", "committed")
KEY_STATUSES = ("active", "retired", "revoked")
CADENCES = ("quarterly",)
REVIEW_STATUSES = ("author_published",)
EDITION_FILES = ("REPORT.md", "account.fixture.json", "edition.snapshot.json", "evaluation.json", "release.json")
SNAPSHOT_NAME = "edition.snapshot.json"
FIXTURE_FIELDS = ("account_id", "cash", "equity", "positions", "observed_at", "market_open", "open_orders",
                  "quotes", "assets")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
QUARTER = re.compile(r"^[0-9]{4}-Q[1-4]$")
PUBLIC_KEY = re.compile(r"^[A-Za-z0-9+/]{43}=$")
# Canonical encoding only: the unused low bits of the last character are zero, so one key has one spelling.
CANONICAL_PUBLIC_KEY = re.compile(r"^[A-Za-z0-9+/]{42}[AEIMQUYcgkosw048]=$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
HISTORY_PATH = re.compile(r"^history/[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")


# Structure ---------------------------------------------------------------------

def identifier(value, what):
    require(isinstance(value, str) and IDENTIFIER.fullmatch(value), f"Invalid {what}")


def identifier_list(values, what, *, minimum=0):
    require(isinstance(values, list) and minimum <= len(values) <= 100, f"Invalid {what} list")
    for value in values:
        identifier(value, what)
    require(len(values) == len(set(values)), f"Duplicate {what}")


def scope_list(values, what):
    require(isinstance(values, list) and 0 < len(values) <= 100 and
            all(isinstance(v, str) and 0 < len(v) <= 100 for v in values) and len(values) == len(set(values)),
            f"Invalid {what}: 1 to 100 distinct entries of 1 to 100 characters")


def text(value, limit, what):
    require(isinstance(value, str) and 0 < len(value) <= limit, f"Invalid {what}: 1 to {limit} characters")


def calendar_date(value, what):
    require(isinstance(value, str) and DATE.fullmatch(value), f"Invalid {what}: use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Refused(f"Invalid {what}: use YYYY-MM-DD") from exc


def validate_themes(document):
    fields(document, ("format", "themes"))
    require(document["format"] == THEMES_FORMAT, "Unsupported themes format")
    themes = document["themes"]
    require(isinstance(themes, list) and len(themes) <= 1000, "Invalid themes list")
    for theme in themes:
        fields(theme, THEME_FIELDS)
        identifier(theme["theme_id"], "theme ID")
        text(theme["title"], 200, "theme title")
        scope_list(theme["geographies"], "theme geographies")
        scope_list(theme["policy_ids"], "theme policy IDs")
        require(theme["status"] in THEME_STATUSES, "Theme status must be researched, in_progress or committed")
        identifier_list(theme["author_ids"], "theme author ID")
        identifier_list(theme["product_ids"], "theme product ID")
        calendar_date(theme["committed_on"], "committed_on date")
        quarter = theme["latest_public_quarter"]
        require(quarter is None or (isinstance(quarter, str) and QUARTER.fullmatch(quarter)),
                "latest_public_quarter must be YYYY-QN or null")
    ids = [theme["theme_id"] for theme in themes]
    require(len(ids) == len(set(ids)), "Duplicate theme ID")
    return document


def validate_authors(document):
    fields(document, ("format", "authors"))
    require(document["format"] == AUTHORS_FORMAT, "Unsupported authors format")
    authors = document["authors"]
    require(isinstance(authors, list) and len(authors) <= 1000, "Invalid authors list")
    for author in authors:
        fields(author, AUTHOR_FIELDS)
        identifier(author["author_id"], "author ID")
        text(author["display_name"], 200, "author display name")
        require(isinstance(author["keys"], list) and 1 <= len(author["keys"]) <= 50,
                "Each author lists 1 to 50 keys")
        for key in author["keys"]:
            fields(key, KEY_FIELDS)
            identifier(key["key_id"], "key ID")
            require(isinstance(key["public_key"], str) and CANONICAL_PUBLIC_KEY.fullmatch(key["public_key"]),
                    "Invalid public key: the canonical standard base64 of 32 bytes, as keygen prints it")
            require(isinstance(key["fingerprint_sha256"], str) and SHA256.fullmatch(key["fingerprint_sha256"]),
                    "Invalid fingerprint: lowercase SHA-256 hex")
            require(key["status"] in KEY_STATUSES, "Key status must be active, retired or revoked")
            calendar_date(key["valid_from"], "valid_from date")
            # Empty for an author registered with a theme before their first product: see check_static.
            identifier_list(key["packages"], "key package")
    authors_ids = [author["author_id"] for author in authors]
    require(len(authors_ids) == len(set(authors_ids)), "Duplicate author ID")
    keys = [key for author in authors for key in author["keys"]]
    require(len({key["key_id"] for key in keys}) == len(keys), "Duplicate key ID")
    require(len({key["public_key"] for key in keys}) == len(keys), "The same public key is listed twice")
    return document


def validate_product(document):
    fields(document, PRODUCT_FIELDS)
    require(document["format"] == PRODUCT_FORMAT, "Unsupported product format")
    for name in ("product_id", "theme_id", "author_id"):
        identifier(document[name], f"product {name}")
    require(document["cadence"] in CADENCES, "Product cadence must be quarterly")
    require(type(document["universe_size"]) is int and 1 <= document["universe_size"] <= 100,
            "universe_size is an integer from 1 to 100")
    text(document["methodology_summary"], 5000, "methodology summary")
    require(isinstance(document["public_history_path"], str) and HISTORY_PATH.fullmatch(document["public_history_path"]),
            "public_history_path must be history/<product_id>")
    require(document["review_status"] in REVIEW_STATUSES, "The only review status is author_published")
    return document


def validate_trust(trust):
    """Every grant of an engine trust file, checked as the engine checks the grant it uses."""
    require(isinstance(trust, dict), "A trust file is an object of key IDs")
    for grant in trust.values():
        fields(grant, ("public_key", "author_id", "packages", "allow_paper"))
        require(isinstance(grant["public_key"], str) and PUBLIC_KEY.fullmatch(grant["public_key"]),
                "Invalid public key: the standard base64 of 32 bytes")
        identifier(grant["author_id"], "author ID")
        require(isinstance(grant["packages"], list), "Invalid trust grant")
        for package in grant["packages"]:
            identifier(package, "package ID")
        require(type(grant["allow_paper"]) is bool, "Invalid trust grant")
    return trust


# Loading and references ---------------------------------------------------------

def read_data(root, relative):
    return read_member_json(Path(root) / relative)


def entries(directory):
    with os.scandir(directory) as found:
        return sorted(found, key=lambda entry: entry.name)


def load(root):
    """Validated catalog files: (themes, authors, products) keyed by ID."""
    root = Path(root)
    require((root / "catalog").is_dir(), "No catalog directory")
    names = {entry.name for entry in entries(root / "catalog")}
    require(names == {"themes.json", "authors.json", "products"},
            "catalog/ holds exactly themes.json, authors.json and products/")
    themes = validate_themes(read_data(root, "catalog/themes.json"))["themes"]
    authors = validate_authors(read_data(root, "catalog/authors.json"))["authors"]
    products = {}
    folder = root / "catalog" / "products"
    require(folder.is_dir() and not folder.is_symlink(), "catalog/products must be a directory")
    for entry in entries(folder):
        require(entry.is_file(follow_symlinks=False) and entry.name.endswith(".json"),
                f"catalog/products/ holds only <product_id>.json files: {entry.name}")
        product = validate_product(read_data(root, f"catalog/products/{entry.name}"))
        require(entry.name == product["product_id"] + ".json",
                f"catalog/products/{entry.name} must be named after its product_id")
        products[product["product_id"]] = product
    return {t["theme_id"]: t for t in themes}, {a["author_id"]: a for a in authors}, products


def check_static(root):
    """Structure, fingerprints and references of the catalog files."""
    themes, authors, products = load(root)
    for theme_id, theme in themes.items():
        for author_id in theme["author_ids"]:
            require(author_id in authors, f"Theme {theme_id} lists unknown author {author_id}")
        for product_id in theme["product_ids"]:
            require(product_id in products, f"Theme {theme_id} lists unknown product {product_id}")
    for product_id, product in products.items():
        theme_id, author_id = product["theme_id"], product["author_id"]
        require(theme_id in themes, f"Product {product_id} names unknown theme {theme_id}")
        require(product_id in themes[theme_id]["product_ids"], f"Theme {theme_id} does not list product {product_id}")
        require(author_id in authors, f"Product {product_id} names unknown author {author_id}")
        require(author_id in themes[theme_id]["author_ids"],
                f"Theme {theme_id} does not list author {author_id} of product {product_id}")
        require(product["public_history_path"] == f"history/{product_id}",
                f"Product {product_id} must keep its public history in history/{product_id}")
    for theme_id, theme in themes.items():
        for product_id in theme["product_ids"]:
            owner = products[product_id]["theme_id"]
            require(owner == theme_id, f"Theme {theme_id} lists product {product_id}, which belongs to theme {owner}")
    listed = {author_id for theme in themes.values() for author_id in theme["author_ids"]}
    for author in authors.values():
        for key in author["keys"]:
            require(fingerprint(key["public_key"]) == key["fingerprint_sha256"],
                    f"Fingerprint mismatch for key {key['key_id']}")
            # A key that lists no products registers an author before their first product. It is accepted only
            # while a theme lists the author, and it grants nothing: trust files and history editions use only
            # keys that list the product in question.
            require(key["packages"] or author["author_id"] in listed,
                    f"Key {key['key_id']} lists no products, which is allowed only while a theme lists author "
                    f"{author['author_id']}")
            for package in key["packages"]:
                require(package in products and products[package]["author_id"] == author["author_id"],
                        f"Key {key['key_id']} lists {package}, which is not a product of author {author['author_id']}")
    return themes, authors, products


# History ----------------------------------------------------------------------

def history_editions(root):
    """(product_id, quarter, directory) for every edition directory under history/, sorted."""
    history = Path(root) / "history"
    if not history.exists():
        return []
    found = []
    for product in entries(history):
        if product.name == "INDEX.md" and product.is_file(follow_symlinks=False):
            continue
        require(product.is_dir(follow_symlinks=False) and IDENTIFIER.fullmatch(product.name),
                f"Unexpected entry in history/: {product.name}")
        for quarter in entries(product.path):
            require(quarter.is_dir(follow_symlinks=False) and QUARTER.fullmatch(quarter.name),
                    f"history/{product.name}/{quarter.name} is not a quarter directory named YYYY-QN")
            found.append((product.name, quarter.name, Path(quarter.path)))
    return found


def registered_since(author, product_id):
    """The earliest valid_from among the author's keys for this product, whatever their status now."""
    dates = [date.fromisoformat(key["valid_from"]) for key in author["keys"] if product_id in key["packages"]]
    return min(dates) if dates else None


def edition_trust(author, product_id):
    """The author's keys for this product that are not revoked, as trust that never allows paper. A key may verify
    an edition published before its own valid_from, so that past editions can be re-signed after a key change;
    check_edition requires that the author already had a key for the product when the edition was published."""
    return {key["key_id"]: {"public_key": key["public_key"], "author_id": author["author_id"],
                            "packages": [product_id], "allow_paper": False}
            for key in author["keys"] if key["status"] != "revoked" and product_id in key["packages"]}


def check_fixture(fixture, payload, where):
    fields(fixture, FIXTURE_FIELDS)
    for name in ("quotes", "assets"):
        require(isinstance(fixture[name], dict) and set(payload["targets"]) <= set(fixture[name]),
                f"{where}/account.fixture.json needs {name} for every target symbol")


def check_edition(root, authors, products, product_id, quarter, directory, now):
    """One history directory: exactly five files, each signature by a valid catalog key, and the binding."""
    where = f"history/{product_id}/{quarter}"
    require(product_id in products, f"{where} has no product entry in catalog/products")
    product = products[product_id]
    author = authors[product["author_id"]]
    require(sorted(scan(directory)) == sorted(EDITION_FILES), f"{where} must hold exactly: {', '.join(EDITION_FILES)}")
    envelope = read_member_json(directory / SNAPSHOT_NAME)
    require(isinstance(envelope, dict) and isinstance(envelope.get("payload"), dict), f"{where}: invalid snapshot")
    published = timestamp(envelope["payload"].get("published_at"))
    since = registered_since(author, product_id)
    require(since is not None and since <= published.date(),
            f"{where} was published on {published.date().isoformat()}, before author {author['author_id']} had a "
            f"catalog key for {product_id}")
    trust = edition_trust(author, product_id)
    documents = {name: read_member_json(directory / name) for name in ("evaluation.json", "release.json")}
    for name, document in ((SNAPSHOT_NAME, envelope), *documents.items()):
        key_id = document.get("key_id") if isinstance(document, dict) else None
        require(key_id in trust, f"{where}/{name} is signed by key {key_id}, which the catalog does not list as a "
                                 f"key of author {author['author_id']} for package {product_id} that is not revoked")
    payload, expired = resolve_historical([envelope], trust, now)
    require(payload["package_id"] == product_id, f"{where}: package {payload['package_id']} is not {product_id}")
    verify_evaluation(documents["evaluation.json"], envelope, trust, now)
    require(documents["release.json"].get("snapshot") == SNAPSHOT_NAME, f"{where}: release must list {SNAPSHOT_NAME}")
    check_release(directory, documents["release.json"], trust, now)
    check_fixture(read_member_json(directory / "account.fixture.json"), payload, where)
    try:
        (directory / "REPORT.md").read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refused(f"{where}/REPORT.md must be UTF-8 text") from exc
    return {"product_id": product_id, "quarter": quarter, "edition_id": payload["edition_id"],
            "information_cutoff": iso(timestamp(payload["information_cutoff"])),
            "valid_until": iso(timestamp(payload["valid_until"])), "universe_size": len(payload["universe"]),
            "expired": expired}


def check_history(root, themes, authors, products, now):
    editions = [check_edition(root, authors, products, product_id, quarter, directory, now)
                for product_id, quarter, directory in history_editions(root)]
    seen = {}
    for edition in editions:
        key = (edition["product_id"], edition["edition_id"])
        require(key not in seen, f"history/{key[0]}: edition {key[1]} appears in both {seen.get(key)} and "
                                 f"{edition['quarter']}")
        seen[key] = edition["quarter"]
    for theme_id, theme in themes.items():
        quarters = [e["quarter"] for e in editions if e["product_id"] in theme["product_ids"]]
        latest = max(quarters) if quarters else None
        require(theme["latest_public_quarter"] == latest,
                f"Theme {theme_id}: latest_public_quarter must be {latest or 'null'}")
    return editions


def summary(editions):
    return [{k: e[k] for k in ("product_id", "quarter", "edition_id", "expired")} for e in editions]


def check(root, now, base=None):
    """catalog check: structure, fingerprints, references and every history edition in historical mode; with a base
    tree, also that catalog/authors.json and history/ only append to it."""
    themes, authors, products = check_static(root)
    editions = check_history(root, themes, authors, products, now)
    result = {"status": "verified", "themes": len(themes), "authors": len(authors),
              "keys": sum(len(a["keys"]) for a in authors.values()), "products": len(products),
              "editions": summary(editions)}
    if base is not None:
        result["append_only"] = check_against_base(base, root)
    return result


def check_append_only(old, new):
    """authors.json relative to its base: entries may be appended and key status may change; nothing else."""
    try:
        validate_authors(old)
    except Refused as exc:
        raise Refused(f"The base catalog/authors.json is invalid: {exc}") from exc
    validate_authors(new)
    message = "catalog/authors.json is append-only: "
    require(new["format"] == old["format"], message + "the format changed")
    require(len(new["authors"]) >= len(old["authors"]), message + "an author was removed")
    for before, after in zip(old["authors"], new["authors"]):
        name = before["author_id"]
        require(after["author_id"] == name, message + f"author {name} was removed, renamed or moved")
        require(after["display_name"] == before["display_name"], message + f"the display name of {name} changed")
        require(len(after["keys"]) >= len(before["keys"]), message + f"a key of {name} was removed")
        for key_before, key_after in zip(before["keys"], after["keys"]):
            key = key_before["key_id"]
            packages = key_after["packages"]
            require(packages[:len(key_before["packages"])] == key_before["packages"],
                    message + f"a package of key {key} was removed or reordered")
            require({**key_after, "status": key_before["status"], "packages": key_before["packages"]} == key_before,
                    message + f"key {key} was edited; only its status may change and packages may be appended")
    return True


def edition_content(directory, where):
    """What re-signing keeps: the snapshot and evaluation payloads, the report and the account fixture."""
    content = {}
    for name in (SNAPSHOT_NAME, "evaluation.json"):
        document = read_member_json(directory / name)
        require(isinstance(document, dict) and isinstance(document.get("payload"), dict),
                f"{where}/{name} is not a signed document")
        content[name] = digest(document["payload"])
    for name in ("REPORT.md", "account.fixture.json"):
        content[name] = file_sha256(directory / name)
    return content


def signing_key(path):
    document = read_member_json(path)
    return document.get("key_id") if isinstance(document, dict) else None


def check_history_append_only(base, root, authors):
    """history/ relative to its base. An existing edition keeps its payloads, report and fixture; only its
    signatures may change. An edition may disappear only if every signature it had in the base was made with a key
    that the catalog now lists as revoked: that is how an edition forged with an exposed key is withdrawn."""
    message = "history/ is append-only: "
    revoked = {key["key_id"] for author in authors.values() for key in author["keys"] if key["status"] == "revoked"}
    before = {(product_id, quarter): path for product_id, quarter, path in history_editions(base)}
    after = {(product_id, quarter): path for product_id, quarter, path in history_editions(root)}
    for (product_id, quarter), path in before.items():
        where = f"history/{product_id}/{quarter}"
        if (product_id, quarter) not in after:
            signers = {signing_key(path / name) for name in (SNAPSHOT_NAME, "evaluation.json", RELEASE_NAME)}
            require(signers <= revoked, message + f"{where} was removed; only an edition whose signatures are all "
                                                   f"by revoked keys may be removed")
            continue
        require(edition_content(after[product_id, quarter], where) == edition_content(path, where),
                message + f"{where} changed; an existing edition may only be re-signed, keeping its payloads, "
                          f"REPORT.md and account.fixture.json")
    return True


def check_against_base(base, root):
    """catalog/authors.json and history/ relative to a base tree, such as the base branch of a pull request."""
    base = Path(base)
    require(base.is_dir(), "Base directory not found")
    _, authors, _ = check_static(root)
    if os.path.lexists(base / "catalog" / "authors.json"):
        check_append_only(read_member_json(base / "catalog" / "authors.json"), read_data(root, "catalog/authors.json"))
    return check_history_append_only(base, root, authors)


def resign_edition(source, output, private, key_id, now):
    """Copy a history edition directory to a new directory with its snapshot, evaluation and release signed by
    another key. Payloads stay identical and the report and fixture are copied byte for byte, so every hash and
    the history index stay the same. Comparing the source with its release.json catches accidental edits only:
    the old signature is not checked, because its key may be revoked. What proves an edition unchanged is the
    comparison with the base branch (check_history_append_only)."""
    source, output = Path(source), Path(output)
    require(sorted(scan(source)) == sorted(EDITION_FILES), f"{source} must hold exactly: {', '.join(EDITION_FILES)}")
    snapshot, evaluation, release = (read_member_json(source / name)
                                     for name in (SNAPSHOT_NAME, "evaluation.json", RELEASE_NAME))
    for name, document in ((SNAPSHOT_NAME, snapshot), ("evaluation.json", evaluation)):
        require(isinstance(document, dict) and isinstance(document.get("payload"), dict),
                f"{source.name}/{name} is not a signed document")
    require(snapshot.get("kind") == "snapshot", f"{source.name}/{SNAPSHOT_NAME} is not a signed snapshot")
    require(isinstance(release, dict) and release.get("files") == inventory(source),
            f"The files of {source} no longer match its release.json; re-sign only an unchanged edition")
    payload = snapshot["payload"]
    require(payload.get("purpose") == "demo", "Only demo editions, as under history/, are re-signed this way")
    signed = authoring.sign_snapshot(private, key_id, payload, now, as_of=payload.get("published_at"))
    signed_evaluation = authoring.sign_evaluation(private, key_id, evaluation.get("payload"), signed, now)
    copies = {}
    for name in ("REPORT.md", "account.fixture.json"):
        with open_member(source / name) as stream:
            copies[name] = stream.read()
    try:
        output.mkdir()
    except FileExistsError as exc:
        raise Refused(f"{output} already exists; resign-edition writes a new directory") from exc
    write_new(output / SNAPSHOT_NAME, signed)
    write_new(output / "evaluation.json", signed_evaluation)
    for name, data in copies.items():
        with open(output / name, "xb") as stream:
            stream.write(data)
    write_new(output / RELEASE_NAME, authoring.sign_release(private, key_id, output, SNAPSHOT_NAME, now))
    return {"status": "re-signed", "source": str(source), "output": str(output), "key_id": key_id,
            "package_id": payload["package_id"], "edition_id": payload["edition_id"], "sha256": digest(payload)}


# Trust files and the history index ---------------------------------------------------

def product_trust(root, product_id, allow_paper=False):
    """An engine trust file for one product. Revoked keys are left out; retired keys never allow paper."""
    _, authors, products = check_static(root)
    require(product_id in products, f"Unknown product {product_id}")
    author = authors[products[product_id]["author_id"]]
    trust = {key["key_id"]: {"public_key": key["public_key"], "author_id": author["author_id"],
                             "packages": [product_id], "allow_paper": allow_paper and key["status"] == "active"}
             for key in author["keys"] if key["status"] != "revoked" and product_id in key["packages"]}
    require(trust, f"The catalog lists no valid key for product {product_id}")
    return validate_trust(trust)


def write_trust(root, product_id, out, allow_paper=False):
    trust = product_trust(root, product_id, allow_paper)
    return {"status": "written", "product_id": product_id, "output": write_new(out, trust),
            "keys": sorted(trust), "allow_paper": any(grant["allow_paper"] for grant in trust.values())}


def render_index(editions):
    lines = ["# Public history", "",
             "Generated by `public-pilot history index`; do not edit by hand. Every edition is signed by its",
             "author and is not yet independently reviewed. `Expired` is as of the last regeneration.", ""]
    if not editions:
        return "\n".join(lines + ["No editions yet."]) + "\n"
    lines += ["| Product | Quarter | Edition | Information cutoff | Valid until | Universe size | Expired |",
              "| --- | --- | --- | --- | --- | ---: | --- |"]
    lines += [f"| {e['product_id']} | {e['quarter']} | {e['edition_id']} | {e['information_cutoff']} | "
              f"{e['valid_until']} | {e['universe_size']} | {'yes' if e['expired'] else 'no'} |" for e in editions]
    return "\n".join(lines) + "\n"


def history_index(root, now, check_only=False):
    """Regenerate history/INDEX.md from verified editions; with check_only, refuse if the file differs."""
    themes, authors, products = check_static(root)
    editions = check_history(root, themes, authors, products, now)
    expected = render_index(editions)
    path = Path(root) / "history" / "INDEX.md"
    require(not path.is_symlink(), "history/INDEX.md must not be a link")
    if check_only:
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        require(current == expected, "history/INDEX.md is out of date; run public-pilot history index")
        return {"status": "current", "path": "history/INDEX.md", "editions": summary(editions)}
    path.parent.mkdir(exist_ok=True)
    path.write_text(expected, encoding="utf-8")
    return {"status": "written", "path": "history/INDEX.md", "editions": summary(editions)}
