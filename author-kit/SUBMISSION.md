# What an author hands over each quarter

Every item is data: JSON or Markdown. A submission never contains executable
code, archives, credentials or private keys. Create and check each item with
the commands in [docs/AUTHORING.md](../docs/AUTHORING.md).

1. **Signed snapshot.** The full edition, signed with `public-pilot sign
   snapshot`. A full snapshot is always supplied, even when a delta is too.
2. **Signed delta, if any.** When the edition updates the previous one, the
   delta from `public-pilot sign delta`. It must reproduce exactly the payload
   of the full snapshot.
3. **Signed evaluation.** Scores, ranks, decisions and weights for every
   company in the universe, from `public-pilot sign-evaluation`, bound to the
   snapshot by its hash and signed with the same key.
4. **Report.** The readable report, for example the output of
   `public-pilot render-evaluation` with your own explanation added.
5. **Evidence list.** The `evidence` field of the payload: every source you
   relied on, with its publication time, none later than the information
   cutoff.
6. **News configuration.** The symbols, aliases, sources and monitoring window
   for the news addon, checked with `public-pilot validate-news-config FILE
   --payload PAYLOAD.json`. It contains no thresholds, prompts or scoring
   rules.

For a past quarter published free under `history/<product_id>/<YYYY-QN>/`, the
directory holds exactly five files: `edition.snapshot.json` (with
`purpose: demo`), `evaluation.json`, `REPORT.md`, `account.fixture.json` (a
fictional account with quotes for every target, for offline previews) and
`release.json` from `public-pilot sign release`. It must pass
`public-pilot verify-bundle` and `public-pilot catalog check`.

Before you hand anything over, confirm that your key is listed as `active` for
the product in `catalog/authors.json`, that its fingerprint is the one you
generated, and that you have never changed the content of an edition ID you
already published. If your key may have been exposed, stop and follow
[SECURITY.md](../SECURITY.md) first: revoke it, list a new key, and re-sign
your editions with `public-pilot resign-edition`.
