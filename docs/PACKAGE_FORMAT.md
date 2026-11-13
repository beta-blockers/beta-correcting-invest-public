# Research package format, version 1

Packages are UTF-8 JSON data, at most 2,000,000 bytes per document and per retained
proof chain. Duplicate keys, non-finite JSON numbers, unknown package fields, and
unknown envelope versions are rejected. No archives, executable extensions,
dynamic imports, or network source-fetching directives are accepted.

## Signed envelope

Each envelope has exactly these fields:

| Field | Meaning |
| --- | --- |
| `format` | `public-pilot-envelope-v1` |
| `kind` | `snapshot` or `delta` |
| `key_id` | Entry in the consumer's local trust file |
| `payload` | Snapshot or delta document below |
| `signature` | Standard-base64 Ed25519 signature |

The signed bytes are the whole envelope **excluding `signature`**, encoded using
Python `json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
allow_nan=False).encode("utf-8")`. This is this format's explicit canonicalization,
not a claim of RFC 8785 compliance. Use string decimals for all target weights;
avoid floating-point numbers. Package hashes use SHA-256 over the canonical
**snapshot payload**, not the signature or envelope.

The `public-pilot` command includes the key generation, validation and signing
tools that authors use; see [authoring](AUTHORING.md). The tests use freshly
generated ephemeral identities.

## Snapshot payload

All fields are required; no additional fields are accepted.

| Field | Contract |
| --- | --- |
| `package_id`, `edition_id`, `author_id` | 1–96 ASCII identifier characters: letters, digits, period, underscore, hyphen; first character alphanumeric |
| `engine_major` | Integer `1` |
| `purpose` | `demo` or `paper`; never `live` |
| `information_cutoff` | Timezone-aware ISO timestamp bounding evidence publication |
| `published_at` | Timezone-aware ISO timestamp at or after cutoff |
| `valid_until` | Exclusive expiry, strictly after publication |
| `geographies`, `policy_ids` | Nonempty lists of declared coverage identifiers |
| `universe` | Explicit set of permitted symbols, including any intended exits |
| `targets` | Symbol → decimal-string portfolio weight, each 0–1, total at most 1 |
| `research` | Readable research text, at most 500,000 characters |
| `evidence` | List of `{title, url, published_at}` references; HTTPS URLs are never fetched |

Scope lists contain at most 100 unique entries; the evidence list contains at most
1,000 references. The runtime validates declared scope and dates. It does not
investigate whether a company's policy eligibility or an author's claim is true.

The consumer can inspect historical expired editions with `show`. New plans and
new submissions require a current, trusted edition. Package validity is a research
freshness claim; subscription/payment expiry is a separate platform concern.

## Historical mode

Normal verification checks the final document as of the current time, so an
edition is refused once `valid_until` has passed. Historical mode makes past
editions readable without making them tradable. It is defined once, as
`packages.resolve_historical(proofs, trust, now)`: the chain is resolved with
every member validated as of its own `published_at`, the result is refused as
`Future-dated research` if its `published_at` is later than `now`, and the call
returns the payload together with `expired`, which is true when `now` is at or
after `valid_until`.

- `verify FILE --allow-expired` and `install FILE --allow-expired` use historical
  mode for the final document. Their output always includes `"expired"`; it is
  `false` without the flag, whose behaviour and messages are unchanged.
- Historical mode relaxes expiry only. The signature, trust scope for the package
  and author, `allow_paper` for `paper` editions, the rule that `published_at`
  must advance over the installed edition, the rule that the cutoff cannot move
  backwards, and the rule that an existing edition ID cannot be replaced all
  still apply. An expired edition can therefore never replace a newer installed
  one.
- `preview --offline` reads an installed edition even if it has expired. The
  resulting plan is marked `offline: true` and can never be executed.
- Live `preview` and `execute-paper` always require a current edition. No order
  is ever submitted for an expired edition.
- The read-only commands `verify-bundle`, `verify-evaluation`, `catalog check`
  and `history index` use historical mode and report `expired`.

## Delta payload

A delta payload contains exactly `package_id`, `base_sha256`, `result_sha256`,
and `replace`. The replacement map replaces whole top-level snapshot fields.
It cannot change `package_id`, `author_id`, or `purpose`. Arrays and the complete
`targets` map replace their previous values; this is not JSON Merge Patch.

The base hash must match the installed edition. Applying `replace` must produce
the declared result hash and a fully valid snapshot. Edition ID must change,
publication must advance, and the information cutoff cannot move backwards.
The delta is independently signed by a locally trusted key authorized for the
same package and author. Each installation stores the original signed snapshot
and the complete signed delta chain; they are reverified before use.

At most 32 envelopes are retained per chain. Supply a fresh independently signed
snapshot to reset a long chain. An expired base can receive a current update.
Installing an older edition or changing the contents of an existing edition ID
is refused. Reinstalling the active identical snapshot is harmless; replaying an
already applied delta fails its base check without changing installed state.

Because installed proofs are reverified with the current trust file, `show`,
`preview` and `execute-paper` refuse an edition whose chain needs a key that has
been removed from it. A full snapshot that verifies with the current trust file
still installs over such an edition: the rules above then compare it with the
installed edition as it was verified when it was installed, and when it is the
same edition signed again with another key, its proofs replace the stored ones.
A delta needs a base that verifies, so it is refused until a full snapshot is
installed. Installing never changes plans or order records.

This is a consumer research-delta format. It does not depend on the private
repository's Git source-snapshot materializer or its research history.

## Evaluation document

A payload has no field for scores and refuses unknown fields, so an author's
scores go in a companion document, signed by the same author key and bound to
one edition by hash:

```json
{"format": "public-pilot-evaluation-v1", "key_id": "...", "signature": "...",
 "payload": {"package_id": "...", "edition_id": "...", "author_id": "...",
             "package_sha256": "...", "as_of": "...",
             "method": {"name": "...", "version": "...", "description": "..."},
             "thresholds": {"NAME": "DECIMAL"},
             "companies": {"SYMBOL": {"rank": 1, "composite": "DECIMAL",
                                      "components": {"NAME": "DECIMAL"},
                                      "decision": "include", "weight": "DECIMAL",
                                      "note": "..."}},
             "defaults_disclosed": ["..."]}}
```

| Field | Contract |
| --- | --- |
| `package_id`, `edition_id`, `author_id` | Identifiers equal to those of the bound snapshot |
| `package_sha256` | SHA-256 of the bound snapshot payload, as `validate`, `sign` and `install` print it |
| `as_of` | Timezone-aware ISO timestamp of the scores |
| `method` | `name` (1–200 characters), `version` (1–50), `description` (at most 20,000) |
| `thresholds` | At most 40 names mapped to decimal strings |
| `companies` | Exactly the symbols of the snapshot's `universe`, each mapped to a company entry |
| `defaults_disclosed` | At most 200 statements (1–1,000 characters each), one for every factor set to a neutral or default value |

Each company entry has exactly `rank`, `composite`, `components`, `decision`,
`weight` and `note`:

- `rank` is an integer. Ranks are a permutation of 1 to n in descending
  `composite` order; tied composites may be ranked either way.
- `components` holds at most 40 named scores. Names are chosen by the author
  (1–64 letters, digits, spaces, `.`, `_` or `-`), because each author uses
  their own method.
- `decision` is `include`, `exclude`, `exit`, `reentry` or `zero_weight`.
- `weight` equals the payload's target for that symbol, or `0` if it has none.
- `note` is text of at most 2,000 characters and may be empty.

Every number is a plain decimal string: an optional minus sign, at most 15
integer digits without leading zeros, and at most 18 fractional digits; no
exponent, plus sign or spaces. Weights lie between 0 and 1. Unknown members are
refused at every level, and documents are strict JSON as elsewhere.

Signing and canonical form are identical to the envelope: every member except
`signature`, serialized as above, signed with Ed25519 by a key trusted for that
`package_id` and `author_id`. `public-pilot sign-evaluation` requires the
edition's snapshot, signed with the same key, and verifies the evaluation
against it before writing. `public-pilot verify-evaluation FILE --snapshot FILE`
resolves the snapshot in historical mode and reports `expired`.
`public-pilot render-evaluation FILE` prints a Markdown table of rank, symbol,
components, composite, decision and weight; it checks structure only, so verify
the signature separately.

## Release inventory

A release inventory signs every file of a data-only bundle, such as a quarter
under `history/`. `public-pilot sign release DIR SNAPSHOT` writes
`DIR/release.json` with exactly these fields:

| Field | Contract |
| --- | --- |
| `format` | `public-pilot-release-v1` |
| `key_id` | Entry in the reader's trust file, trusted for `package_id` |
| `package_id` | Package ID of the bundled snapshot |
| `snapshot` | Path of the full signed snapshot, relative to `DIR` |
| `files` | Every regular file under `DIR` except the root `release.json`, mapped to the lowercase SHA-256 hex of its bytes; 1–500 entries |
| `signature` | Standard-base64 Ed25519 signature over the canonical document without `signature`, as for envelopes |

Listed paths are relative POSIX paths with no empty, `.` or `..` component, no
backslash and no control character. `public-pilot verify-bundle DIR` checks the
signature and the key's trust scope, that every listed file exists with its
hash, and that `DIR` holds no other regular file except the root `release.json`
itself: bundles are data only, so caches, hidden files and any other stray file
are rejected. Symbolic links, hard links and special files are refused. Finally
the listed snapshot must resolve in historical mode and belong to the release's
package and author; the output reports `expired`. Sign the release with the
same key as the snapshot: the signer verifies the result before writing it.

## Local trust file

```json
{
  "publisher-key-1": {
    "public_key": "BASE64_OF_32_BYTE_ED25519_PUBLIC_KEY",
    "author_id": "author-identifier",
    "packages": ["specific-product-id"],
    "allow_paper": true
  }
}
```

Keys are explicitly scoped to products; there is no wildcard grant. The demo key
must stay `allow_paper: false`. Without `allow_paper`, a key's `demo` editions
can be verified, installed, shown and previewed offline, and its `paper`
editions are refused. A live preview or `execute-paper` needs `allow_paper` for
every key in the edition's proof chain, for `demo` and `paper` editions alike
(engine 0.4.0 and later; earlier engines never trade `demo` editions).

Removing a key invalidates editions whose retained proof chain needs it. For
key rotation, authorize the new key locally and obtain a fresh signed snapshot.
Neither a package nor a delta can modify this trust file.

## JSON Schemas

`schemas/` holds JSON Schemas (draft 2020-12) for the snapshot payload, the delta
payload, the envelope, the trust file, the evaluation, the release inventory, the
news configuration and the three catalog files. They express structure only:
required and forbidden members, types, enumerations, string patterns, and length
and count limits. They cannot express the engine's relational and time-based
rules: cutoff ≤ publication < expiry, target weights that sum to at most 1,
targets within the universe, evidence dated no later than the cutoff, delta and
evaluation hashes, signatures and trust. JSON Schema also counts `1.0` as an
integer where the engine requires an integer literal.

**A document a schema accepts can still be refused by the engine. The Python
validator is authoritative.** Use the schemas for editor support and quick
structural checks, and run `public-pilot validate`, which needs no extra
library, before signing. The engine never imports a schema library.
