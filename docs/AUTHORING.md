# Authoring a research package

This guide is for authors who publish research in the package format that the
engine reads. You keep your own research methods and code; what you publish is
signed data: a payload with your universe, target weights, research text and
evidence, an evaluation with your scores, and a release inventory. Every
command here is offline: none contacts a broker, a model or any network
service.

## Before you start

Install the engine as described in [ENGINE.md](ENGINE.md) and run the commands
below from the repository root. The walkthrough builds a fictional edition from
the templates in `author-kit/`. It works in a scratch copy of `catalog/` and
`history/` and keeps its fictional key in a temporary directory, so nothing in
your checkout changes. The guidance after the walkthrough explains how to do
each step for real research.

## Walkthrough

### 1. Prepare a workspace and a key

```sh
export PATH="$PWD/.venv/bin:$PATH"
WORK="$(mktemp -d)"
KEYS="$(mktemp -d)"
cp -R catalog history "$WORK/"
public-pilot keygen --out "$KEYS/example-author.key" > "$KEYS/example-author.public.json"
cat "$KEYS/example-author.public.json"
```

`keygen` writes a raw 32-byte Ed25519 private key with mode 0600 and prints
the public key and its fingerprint (the SHA-256 of the raw public key). It never
overwrites a file and refuses any path inside a Git checkout.

### 2. Write and validate the payload

```sh
cp author-kit/payload.template.json "$WORK/payload.json"
public-pilot validate "$WORK/payload.json" --as-of 2020-04-01T14:00:00+00:00
```

`author-kit/payload.FIELDS.md` explains every field. `validate` runs exactly
the check that `install` runs and prints the first failure, or the payload's
`sha256` when it is valid. Without `--as-of` it checks the payload as of now;
the template is a fictional past edition, so the walkthrough checks it as of
its publication day.

### 3. Sign the snapshot

```sh
EDITION="$WORK/history/example-product/2020-Q2"
mkdir -p "$EDITION"
public-pilot sign snapshot "$WORK/payload.json" "$EDITION/edition.snapshot.json" \
  --key "$KEYS/example-author.key" --key-id example-author-2020 --as-of 2020-04-01T14:00:00+00:00
```

`sign` verifies what it signed before writing it and never overwrites a file.
`--as-of` signs an edition that has already expired, with the self-check run
as of that time; it is accepted only for `purpose: demo`, which is what past
quarters under `history/` use. Sign a current edition without it.

### 4. Sign the evaluation and write the report

```sh
cp author-kit/evaluation.template.json "$WORK/evaluation.json"
public-pilot sign-evaluation "$WORK/evaluation.json" "$EDITION/evaluation.json" \
  --snapshot "$EDITION/edition.snapshot.json" --key "$KEYS/example-author.key" --key-id example-author-2020
public-pilot render-evaluation "$EDITION/evaluation.json" > "$EDITION/REPORT.md"
cp examples/account.json "$EDITION/account.fixture.json"
```

The evaluation's `package_sha256` is the `sha256` that `validate` printed. Its
companies are exactly the universe, and each weight equals the payload's target
or 0. `sign-evaluation` checks all of that against the snapshot, which must be
signed with the same key. Add your own explanation to `REPORT.md` if you like.
The account fixture is a fictional account, with quotes for every target, that
readers use for offline previews.

### 5. List the key, theme and product in the catalog

In a real submission you make these changes in your pull request; here they go
into the scratch copy. Editing the files by hand is equally fine.

```sh
python - "$WORK" "$KEYS/example-author.public.json" <<'PY'
import json
import sys
from pathlib import Path

work, key = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())


def update(name, change):
    path = work / "catalog" / name
    document = json.loads(path.read_text()) if path.exists() else {}
    change(document)
    path.write_text(json.dumps(document, indent=2) + "\n")


update("authors.json", lambda d: d["authors"].append({
    "author_id": "example-author", "display_name": "Example Author (fictional)",
    "keys": [{"key_id": "example-author-2020", "public_key": key["public_key"],
              "fingerprint_sha256": key["fingerprint_sha256"], "status": "active",
              "valid_from": "2020-01-01", "packages": ["example-product"]}]}))
update("themes.json", lambda d: d["themes"].append({
    "theme_id": "example-theme", "title": "Fictional example theme", "geographies": ["SYNTHETIC"],
    "policy_ids": ["fictional-grant-program"], "status": "researched", "author_ids": ["example-author"],
    "product_ids": ["example-product"], "committed_on": "2020-01-01", "latest_public_quarter": "2020-Q2"}))
update("products/example-product.json", lambda d: d.update({
    "format": "public-pilot-product-v1", "product_id": "example-product", "theme_id": "example-theme",
    "author_id": "example-author", "cadence": "quarterly", "universe_size": 3,
    "methodology_summary": "Fictional example product built from the author kit templates.",
    "public_history_path": "history/example-product", "review_status": "author_published"}))
PY
```

### 6. Sign the release inventory and check everything

```sh
public-pilot sign release "$EDITION" edition.snapshot.json \
  --key "$KEYS/example-author.key" --key-id example-author-2020
public-pilot catalog trust "$WORK" --product example-product --out "$WORK/trust.json"
public-pilot --trust "$WORK/trust.json" verify-bundle "$EDITION"
public-pilot --trust "$WORK/trust.json" verify-evaluation "$EDITION/evaluation.json" \
  --snapshot "$EDITION/edition.snapshot.json"
public-pilot history index "$WORK"
public-pilot catalog check "$WORK"
```

The release lists every file of the directory except `release.json` itself, so
sign it last. `verify-bundle` proves the files are unchanged; `catalog check`
also proves that the evaluation belongs to the edition and that the key is
listed for this author and product. Both report `"expired": true`, because the
fictional edition is a past quarter.

### 7. Check the news configuration

```sh
cp author-kit/news-config.template.json "$WORK/news-config.json"
public-pilot validate-news-config "$WORK/news-config.json" --payload "$WORK/payload.json"
```

The news configuration names the symbols, their aliases and optional SEC CIK
numbers, the sources to monitor and the monitoring window. With `--payload`,
its symbols must belong to the universe and `epoch_end` must not be later than
the edition's `valid_until`. It holds no thresholds, prompts or scoring rules.

### 8. Issue an update as a delta and a full snapshot

```sh
python - "$WORK/payload.json" "$WORK/payload-r2.json" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1]))
payload.update(edition_id="example-product-2020-q2-r2", published_at="2020-04-15T13:00:00+00:00",
               targets={"DEMOA": "0.45", "DEMOB": "0.30"})
json.dump(payload, open(sys.argv[2], "w"), indent=2)
PY
mkdir "$WORK/updates"
public-pilot sign snapshot "$WORK/payload-r2.json" "$WORK/updates/r2.snapshot.json" \
  --key "$KEYS/example-author.key" --key-id example-author-2020 --as-of 2020-04-15T14:00:00+00:00
public-pilot sign delta "$WORK/payload.json" "$WORK/payload-r2.json" "$WORK/updates/r2.delta.json" \
  --key "$KEYS/example-author.key" --key-id example-author-2020 --as-of 2020-04-15T14:00:00+00:00
public-pilot --state "$WORK/state" --trust "$WORK/trust.json" install "$EDITION/edition.snapshot.json" --allow-expired
public-pilot --state "$WORK/state" --trust "$WORK/trust.json" install "$WORK/updates/r2.delta.json" --allow-expired
public-pilot --state "$WORK/fresh" --trust "$WORK/trust.json" install "$WORK/updates/r2.snapshot.json" --allow-expired
```

The delta applied to the first edition and the full snapshot of the second
report the same `sha256`.

### 9. Replace the key and re-sign the edition

When a key may have been exposed, the author revokes it, lists a new key and
re-signs the edition with the new key. `BASE` keeps the tree as it was before,
the way a pull request's base branch does.

```sh
BASE="$(mktemp -d)"
cp -R "$WORK/catalog" "$WORK/history" "$BASE/"
public-pilot keygen --out "$KEYS/example-author-2.key" > "$KEYS/example-author-2.public.json"
python - "$WORK/catalog/authors.json" "$KEYS/example-author-2.public.json" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

path, key = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())
document = json.loads(path.read_text())
keys = next(a for a in document["authors"] if a["author_id"] == "example-author")["keys"]
keys[0]["status"] = "revoked"
keys.append({"key_id": "example-author-2", "public_key": key["public_key"],
             "fingerprint_sha256": key["fingerprint_sha256"], "status": "active",
             "valid_from": datetime.now(timezone.utc).date().isoformat(), "packages": ["example-product"]})
path.write_text(json.dumps(document, indent=2) + "\n")
PY
public-pilot resign-edition "$EDITION" "$WORK/resigned" \
  --key "$KEYS/example-author-2.key" --key-id example-author-2
rm -r "$EDITION"
mv "$WORK/resigned" "$EDITION"
public-pilot catalog check "$WORK" --base "$BASE"
public-pilot history index "$WORK" --check
```

The new key was listed today, yet it may sign the 2020 edition, because the
author already had a key for the product when the edition was published.
`resign-edition` writes a new directory, keeps the payloads identical and
copies the report and fixture byte for byte, so the edition's `sha256` and its
line in `history/INDEX.md` do not change. `--base` checks exactly that against
the earlier tree, as continuous integration does for a pull request.

A reader who installed the update in step 8 writes a trust file without the
revoked key. `show` then refuses the installed edition, because the revoked
key signed it. The reader installs the update signed again with the new key
into the same state directory:

```sh
public-pilot catalog trust "$WORK" --product example-product --out "$WORK/trust-2.json"
public-pilot --state "$WORK/state" --trust "$WORK/trust-2.json" show example-product \
  || echo "Refused as expected: the revoked key signed the installed edition"
public-pilot sign snapshot "$WORK/payload-r2.json" "$WORK/updates/r2.resigned.json" \
  --key "$KEYS/example-author-2.key" --key-id example-author-2 --as-of 2020-04-15T14:00:00+00:00
public-pilot --state "$WORK/state" --trust "$WORK/trust-2.json" install "$WORK/updates/r2.resigned.json" --allow-expired
public-pilot --state "$WORK/state" --trust "$WORK/trust-2.json" show example-product > "$WORK/shown.json"
```

Installing the re-signed snapshot of the same edition replaces its proofs, and
the state directory keeps its plans and order records.
[SECURITY.md](../SECURITY.md) lists every step for authors and readers.

## Registering before your first product

A new author joins in two pull requests, as [CONTRIBUTING.md](../CONTRIBUTING.md)
describes: first an author entry and a committed theme, before any product
exists; later the first product. This walkthrough runs both with a fictional
author, in a scratch copy of `catalog/` and `history/`. `BASE` holds the tree
as it was before each pull request, the way a pull request's base branch does.

### 1. Register the author and a theme

The new key lists no products: `"packages": []`. The catalog accepts that only
because the new theme lists the author.

```sh
export PATH="$PWD/.venv/bin:$PATH"
WORK="$(mktemp -d)"
BASE="$(mktemp -d)"
KEYS="$(mktemp -d)"
cp -R catalog history "$WORK/"
cp -R catalog history "$BASE/"
public-pilot keygen --out "$KEYS/new-author.key" > "$KEYS/new-author.public.json"
python - "$WORK" "$KEYS/new-author.public.json" <<'PY'
import json
import sys
from pathlib import Path

work, key = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())


def update(name, change):
    path = work / "catalog" / name
    document = json.loads(path.read_text())
    change(document)
    path.write_text(json.dumps(document, indent=2) + "\n")


update("authors.json", lambda d: d["authors"].append({
    "author_id": "new-author", "display_name": "New Author (fictional)",
    "keys": [{"key_id": "new-author-2020", "public_key": key["public_key"],
              "fingerprint_sha256": key["fingerprint_sha256"], "status": "active",
              "valid_from": "2020-01-01", "packages": []}]}))
update("themes.json", lambda d: d["themes"].append({
    "theme_id": "new-theme", "title": "Fictional new theme", "geographies": ["SYNTHETIC"],
    "policy_ids": ["fictional-grant-program"], "status": "committed", "author_ids": ["new-author"],
    "product_ids": [], "committed_on": "2020-01-01", "latest_public_quarter": None}))
PY
public-pilot catalog check "$WORK" --base "$BASE"
```

Until a product is appended to its `packages`, the key grants nothing. No trust
file can be built for a product that does not exist, and the trust files of
other products leave the key out, so nothing it signs verifies:

```sh
public-pilot catalog trust "$WORK" --product new-product --out "$WORK/new-trust.json" \
  || echo "Refused as expected: new-product is not in the catalog yet"
public-pilot catalog trust "$WORK" --product synthetic-example --out "$WORK/example-trust.json"
```

### 2. Register the first product

When the first product is ready, one pull request adds its entry, lists it in
the theme and appends it to the key's `packages`. Appending a product is the
only change besides `status` that the append-only rule allows on a listed key.

```sh
BASE="$(mktemp -d)"
cp -R "$WORK/catalog" "$WORK/history" "$BASE/"
python - "$WORK" <<'PY'
import json
import sys
from pathlib import Path

work = Path(sys.argv[1])


def update(name, change):
    path = work / "catalog" / name
    document = json.loads(path.read_text()) if path.exists() else {}
    change(document)
    path.write_text(json.dumps(document, indent=2) + "\n")


def list_product(document):
    theme = next(t for t in document["themes"] if t["theme_id"] == "new-theme")
    theme["product_ids"].append("new-product")
    theme["status"] = "in_progress"


def append_package(document):
    author = next(a for a in document["authors"] if a["author_id"] == "new-author")
    author["keys"][0]["packages"].append("new-product")


update("products/new-product.json", lambda d: d.update({
    "format": "public-pilot-product-v1", "product_id": "new-product", "theme_id": "new-theme",
    "author_id": "new-author", "cadence": "quarterly", "universe_size": 3,
    "methodology_summary": "Fictional first product of a new author.",
    "public_history_path": "history/new-product", "review_status": "author_published"}))
update("themes.json", list_product)
update("authors.json", append_package)
PY
public-pilot catalog check "$WORK" --base "$BASE"
public-pilot catalog trust "$WORK" --product new-product --out "$WORK/new-trust.json"
```

The key may now sign editions of `new-product`, and no others. The
[walkthrough](#walkthrough) above shows how to sign and check an edition.

## Guidance

### Guarding your key

Generate your real key in a private directory outside every Git checkout, for
example `mkdir -m 700 ~/.config/public-pilot-keys` followed by
`public-pilot keygen --out ~/.config/public-pilot-keys/YOUR-KEY-ID.key`. The
signing commands refuse a key that is inside a Git checkout, readable by other
users, a symbolic or hard link, or not exactly 32 bytes. Keep an encrypted
offline backup. Never put the private key in a repository, a CI secret, a chat
or an email; tests and continuous integration need no key. The commands find a
Git checkout by its `.git` entry, so also keep the key out of any directory that
a Git repository stored elsewhere tracks, such as a dotfiles work tree, and out
of directories whose access control lists let other users read files. Only the
public key and its fingerprint leave your machine. If the key may have been exposed,
follow [SECURITY.md](../SECURITY.md).

### Cutoff, publication and expiry

Set `information_cutoff` to the true cutoff of your evidence: the latest date
of any source you relied on. It is not the time you compiled the package and
not the time you publish it. `published_at` is when you publish, and
`valid_until` ends the edition's validity, usually at the end of the quarter
it covers, never according to anyone's subscription. Every evidence entry must
be dated no later than the cutoff.

### Writing the evidence list

List every source the research relies on in `evidence`, with a descriptive
title, an `https://` URL without credentials and the source's own publication
time. The engine never fetches these URLs; the list exists so that readers and
reviewers can check your sources.

### Exits

To sell a company that readers may hold, keep its symbol in `universe` and give
it no positive weight in `targets`. The engine refuses to plan when a reader
holds a symbol outside the universe. In the evaluation, record the decision as
`exit` with weight `0`.

### Validating and signing

Run `public-pilot validate` on every payload before signing. Sign a snapshot
and its evaluation with the same key, and sign the release inventory last,
after every other file of the directory is final. Signing commands check their
output before writing it and never overwrite a file.

### Deltas and full snapshots

When an edition updates the previous one, sign a delta from the previous
payload to the new one and also sign the new payload as a full snapshot.
Supply both. The delta applies only to its exact base and must reproduce
exactly the payload of the full snapshot; readers whose installed edition is
different, or who start fresh, install the full snapshot. A delta cannot change
`package_id`, `author_id` or `purpose`, must change `edition_id`, must advance
`published_at`, and cannot move `information_cutoff` backwards.

### Never rewrite an edition

Once an edition ID is published, its content never changes. A correction is a
new edition with a new `edition_id` and a later `published_at`. The engine
refuses to replace an installed edition ID with different content and refuses
to go back to an older edition. Re-signing an edition with a new key, as in
step 9, changes only its signatures.

### Getting your key listed

Readers trust a key only after confirming it through a channel they trust. In
this repository, that channel is `catalog/authors.json`: open a pull request
that appends your author entry, with your `key_id`, `public_key`,
`fingerprint_sha256` (from `keygen`), `status: active`, `valid_from` and the
products it may sign, together with your theme entry, as `CONTRIBUTING.md`
describes. Before your first product exists the key lists none, and a later
pull request adds the product and appends it to the key, as
[Registering before your first product](#registering-before-your-first-product)
shows. Readers then build a trust file with `public-pilot catalog trust`, which
lists your key only for the products it names. Announce the fingerprint through
a second channel too, so that readers can compare it.

### Submissions are data only

A submission contains JSON and Markdown data and nothing else: no executable
code, scripts, archives, notebooks, credentials or keys. `author-kit/SUBMISSION.md`
lists what to hand over each quarter.

### What a signature means

A signature proves which author published a package and that it has not
changed. It does not prove that the research is accurate. Editions are
currently published by their authors without independent review; the catalog
records every product's review status as `author_published`.
