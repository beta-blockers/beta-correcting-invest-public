# Payload fields

`payload.template.json` contains every field of a version 1 payload. All fields
are required and no other field is accepted. Check a payload with
`public-pilot validate PAYLOAD.json`; the engine runs exactly the same check
when it installs an edition. Every value in the template is fictional.

**`package_id`** identifies the product's package. In the catalog a product
publishes all its editions under one package ID equal to its product ID, so a
reader's engine replaces one edition with the next. It uses 1–96 letters,
digits, `.`, `_` or `-`, starting with a letter or digit, and never changes.

**`edition_id`** names this edition, with the same characters as `package_id`.
Every edition gets a new ID, including a corrected one. An edition ID is never
reused for different content.

**`author_id`** is your author ID as listed in `catalog/authors.json`. Readers
trust your key only for this author, and a delta cannot change it.

**`engine_major`** is the integer `1`, the engine version the package is
written for.

**`purpose`** is `demo` or `paper`. A `demo` edition can be read and previewed
offline but never trades. A `paper` edition can be run in a paper account by a
reader whose trust file allows it. Editions published under `history/` are
`demo`. There is no live purpose.

**`published_at`** is the timezone-aware ISO time at which you publish the
edition. It must not be earlier than `information_cutoff`, and each new edition
of a package must have a later `published_at` than the one before.

**`information_cutoff`** is the true cutoff of your evidence: no source you used
may be dated after it. Set it to that date, not to the time you compiled the
package or the time you publish it. It must never move backwards from one
edition to the next.

**`valid_until`** is the exclusive end of the edition's validity, strictly after
`published_at`, usually the end of the quarter the research covers. After it,
the engine opens the edition only for reading and never trades on it.

**`geographies`** lists the regions the research covers, for example country
codes: 1 to 100 distinct entries of 1 to 100 characters.

**`policy_ids`** lists the public programs or policies whose support defines
the field of candidates, with the same limits as `geographies`.

**`universe`** is the explicit set of symbols the edition may hold: 1 to 100
distinct uppercase symbols. Keep an exiting symbol in the universe with no
positive weight so that a reader who holds it can sell it; a symbol held
outside the universe stops planning.

**`targets`** maps symbols of the universe to target weights, written as
decimal strings such as `"0.40"`. Each weight lies between 0 and 1 and the total
is at most 1; the rest stays in cash. A symbol with no target has weight 0.

**`research`** is the readable research text, up to 500,000 characters. It is
shown as data, never run or rendered as HTML. Explain the selection here.

**`evidence`** lists up to 1,000 references as `{title, url, published_at}`:
a title of 1 to 500 characters, an `https://` URL without credentials, and the
source's publication time, which may not be later than `information_cutoff`.
The engine never fetches these URLs; they let readers check your sources.
