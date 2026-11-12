# Contributing

Contributions arrive as pull requests. Continuous integration only validates:
it holds no secrets, publishes nothing and never contacts a broker.

## Ground rules

1. **No merged histories.** A pull request adds or changes specific files. Do
   not merge the history of another repository or branch into this one. Every
   tracked file must be inside the allowlist that `scripts/export_scan.sh`
   enforces.
2. **Trading safety is fixed.** Order planning, execution and the broker client
   (`src/public_pilot/planning.py`, `execution.py`, `broker.py`) do not change
   as a side effect of other work. No change may weaken the fixed paper
   endpoint, the refusal of expired research for live previews and order
   submission, selling before buying, limit-price collars, order limits,
   deterministic order identifiers, or the rule that an uncertain submission is
   never retried.
3. **Existing tests stay as they are.** A change adds tests. It does not edit
   or delete existing tests to make them pass.
4. **Package format version 1 is fixed.** The fields of a version 1 payload do
   not change. New information goes in a separate document, signed by the same
   author and bound to the edition by hash, as the evaluation and release
   documents are.
5. **Commit with your GitHub noreply address.** Every commit's author and
   committer address must be a GitHub noreply address
   (`ID+username@users.noreply.github.com`). Turn on "Keep my email addresses
   private" in your GitHub settings and set `git config user.email` to that
   address. The export scan rejects any other author or committer address, and
   any other address in a tracked file.
6. **Examples are fictional.** Tests, examples and templates use invented
   symbols such as `DEMOA` and invented values. Real research enters this
   repository only as an author-signed edition under `history/`.
7. **No performance figures.** Do not add returns, back-tests, benchmarks or
   any other performance claim anywhere in the repository.
8. **Published history is append-only.** An edition under `history/` is never
   changed, and never removed unless all its signatures are by revoked keys,
   as for an edition forged with an exposed key. After a key change, its
   author re-signs it with `public-pilot resign-edition`, which changes only
   its signatures. Continuous integration checks this against the base branch.

Before opening a pull request, run the tests, `public-pilot catalog check`,
`public-pilot history index --check` and `scripts/export_scan.sh`.

## Proposing a theme

1. Read [docs/AUTHORING.md](docs/AUTHORING.md) and
   [docs/CATALOG.md](docs/CATALOG.md).
2. Generate a signing key with `public-pilot keygen`, in a directory outside
   every Git checkout. Only the public key and its fingerprint go in the pull
   request.
3. In one pull request:
   - append your author entry, with that public key, to
     `catalog/authors.json`. The file is append-only: entries are never
     deleted or edited, except that a key's `status` may change;
   - append your theme to `catalog/themes.json` with `status` set to
     `committed`, your author ID in `author_ids`, today's date in
     `committed_on`, no `product_ids` yet, and `latest_public_quarter` set to
     `null`.
4. Run `public-pilot catalog check` and open the pull request. Describe the
   industry, the geographies and the public programs the theme covers.

A theme moves to `in_progress` while research is under way and to `researched`
once a product has published at least one edition. Products and their public
history are added as described in the authoring guide.

## Submissions are data

Research packages, evaluations, reports and fixtures are JSON or Markdown data.
Never submit executable code, archives, credentials, private keys, or anything
produced from a non-public source you are not allowed to redistribute.
