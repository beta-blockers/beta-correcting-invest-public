# Using the engine

A small Python runtime for **consuming completed research packages**: verify an
edition, read its research, preview its target portfolio, and explicitly execute
the resulting plan in an Alpaca paper account.

The engine does not discover companies, collect policy or financial evidence,
calculate research scores, generate target weights, or call a language model.
Authors supply the completed research and target weights in a signed data package.

For a real-company research example, start with the
[free sample walkthrough](SAMPLE.md). It links the readable report and gives
the exact commands to verify and preview the signed demo without credentials.

## What is included

- Ed25519 publisher verification with locally configured, package-specific trust.
- Strict JSON snapshots and signed deltas with base/result SHA-256 verification.
- Immutable edition records and an inspectable research viewer.
- Current paper-account observations, IEX quotes, and tradability checks.
- Whole-share, long-only planning with customer allocation, concentration, order,
  turnover, quote-age, spread, and price-collar limits.
- Serial paper execution, durable submission intent, restart reconciliation,
  explicit cancellation, and a local order audit.
- A fictional two-company example and offline tests.

Research scoring and target construction happen before publication. New policy
interpretations and target changes require a new signed edition from the author.
An optional, separately distributed addon can supply time-limited activation
decisions for those targets. Execution quotes do not regenerate research.

## Install

Python 3.11+ on Linux or macOS is required. The local execution lock uses `flock`.
Run these commands from a checkout of this repository.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-build-isolation .
. .venv/bin/activate
```

The last line puts `public-pilot` on this terminal's path, as the sample reports'
commands expect. In a new terminal, run `. .venv/bin/activate` again from the
checkout first.

## Try the fictional example without credentials

Run from this checkout. The example contains fictional symbols and invented
values. Its public verification key is trusted for demonstrations only.

```sh
.venv/bin/public-pilot --state .state/demo --trust examples/trust.json verify examples/demo.snapshot.json
.venv/bin/public-pilot --state .state/demo --trust examples/trust.json install examples/demo.snapshot.json
.venv/bin/public-pilot --state .state/demo --trust examples/trust.json show synthetic-example
.venv/bin/public-pilot --state .state/demo --trust examples/trust.json preview synthetic-example --offline examples/account.json
.venv/bin/public-pilot --state .state/demo --trust examples/trust.json install examples/demo.delta.json
.venv/bin/public-pilot --state .state/demo --trust examples/trust.json show synthetic-example
```

Offline previews explicitly advance the fixture's clock to the current time;
they are permanently marked non-executable. No command above contacts a broker,
model, research source, or evidence URL. Research text is displayed as JSON data,
not interpreted as commands or rendered as executable HTML.

The [public history index](../history/INDEX.md) lists the available samples and
past quarters. The fictional past quarter below has expired. Build its trust
file from the catalog, check its signed files, and read it in historical mode.
It can be previewed offline but never traded:

```sh
mkdir -p .state
.venv/bin/public-pilot catalog trust --product synthetic-example --out .state/synthetic-history-trust.json
.venv/bin/public-pilot --trust .state/synthetic-history-trust.json verify-bundle history/synthetic-example/2020-Q1
.venv/bin/public-pilot --trust .state/synthetic-history-trust.json verify-evaluation history/synthetic-example/2020-Q1/evaluation.json --snapshot history/synthetic-example/2020-Q1/edition.snapshot.json
.venv/bin/public-pilot --state .state/history --trust .state/synthetic-history-trust.json install history/synthetic-example/2020-Q1/edition.snapshot.json --allow-expired
.venv/bin/public-pilot --state .state/history --trust .state/synthetic-history-trust.json preview synthetic-example --offline history/synthetic-example/2020-Q1/account.fixture.json
```

Each of these reports `"expired": true` where it applies, and `history/INDEX.md`
lists every edition.

## Read past editions

Every edition expires at its `valid_until`. To read one afterwards, add
`--allow-expired` to `verify` or `install`. The output then reports
`"expired": true`. An installed expired edition can be shown and previewed
offline against a fixture; that plan is marked `offline: true` and can never
execute. Live previews and paper orders always require a current edition, and
every other check (signature, trust scope, no downgrade) still applies. See
[historical mode](PACKAGE_FORMAT.md#historical-mode).

## Use an author-supplied edition

Obtain the author's public key through a trusted channel and place it in your
local trust file, scoped to the relevant package ID. For a product listed in
this repository's catalog, `public-pilot catalog trust --product ID --out FILE`
writes that trust file. Install the signed edition as above. A key embedded in
a downloaded package cannot grant itself trust.

Live previews and paper orders need a current edition and a trust grant with
`allow_paper: true` for every key that signed it, whatever the edition's
`purpose`. A `paper` edition also needs that permission to be verified,
installed or shown; a `demo` edition does not. Installing, showing and offline
previews need no broker account.

### Trade a demo edition on paper

From engine 0.3.1, a current `demo` edition, such as a US sample under
`history/`, can be previewed live and traded on paper once its trust file
allows paper. `--allow-paper` grants that only to the product's active keys.
Use a state directory of its own: a later `paper` edition of the same product
cannot replace a `demo` edition in one state directory.

```sh
mkdir -p .state
.venv/bin/public-pilot catalog trust --product usmaterials --allow-paper --out .state/usmaterials-paper-trust.json
.venv/bin/public-pilot --state .state/usmaterials-paper --trust .state/usmaterials-paper-trust.json install history/usmaterials/2026-Q4/edition.snapshot.json
```

Then follow the [manual steps](#manual-steps-with-your-own-paper-account) with
`--state .state/usmaterials-paper`, `--trust .state/usmaterials-paper-trust.json`
and the package ID `usmaterials`. Earlier engines, and the signed sample
reports written for them, limit `demo` editions to reading and offline
previews.

## Manual steps with your own paper account

Every command in this section uses your own Alpaca **paper** account, or the
local record of a plan made with it. Nothing else in this repository needs broker
credentials. The runtime has a fixed paper endpoint and no live-endpoint switch.

Keep your own paper credentials in your environment: `APCA_API_KEY_ID` and
`APCA_API_SECRET_KEY`. Never put them in a research package or repository.
`examples/paper.env.example` lists the variables; copy it outside Git, restrict it
to your user, and edit it locally:

```sh
umask 077
mkdir -p "$HOME/.config/public-pilot"
cp examples/paper.env.example "$HOME/.config/public-pilot/paper.env"
# Open the copy in your editor and enter your own paper keys and limits.
set -a
. "$HOME/.config/public-pilot/paper.env"
set +a
```

Preview during a regular market session. The preview reads your paper account,
positions and quotes; it does not place orders.

```sh
.venv/bin/public-pilot --state .state/paper --trust trust.json preview YOUR_PACKAGE_ID --allocation "$PILOT_ALLOCATION" --max-order "$PILOT_MAX_ORDER" --max-turnover "$PILOT_MAX_TURNOVER" --max-weight "$PILOT_MAX_WEIGHT"
# Inspect the returned plan, then use its exact plan_id and account_id:
.venv/bin/public-pilot --state .state/paper --trust trust.json execute-paper PLAN_ID --account PAPER_ACCOUNT_ID
.venv/bin/public-pilot --state .state/paper status PLAN_ID
# Run execute-paper again to reconcile an in-flight order and continue.
# To stop outstanding orders belonging to this plan:
.venv/bin/public-pilot --state .state/paper cancel-paper PLAN_ID --account PAPER_ACCOUNT_ID
```

Only `execute-paper` submits orders; only `cancel-paper` requests cancellation.
There is no background scheduler. Use a dedicated paper account without other
strategies or manual orders while a plan is running. A preview is valid for 120
seconds. A `pending` result means the run is unfinished: repeat `execute-paper`
for the **same** plan. A `halted` result names the stock whose order stopped the
plan, for example one the broker refused for insufficient buying power; preview a
fresh plan. Do not delete state or create a replacement plan while a submission
is uncertain. See [operations](OPERATIONS.md) for recovery.

Without `--max-order`, a single order is at most USD 1,000. One share must fit in
an order, so a plan can buy shares priced up to about USD 1,000; the preview
refuses a plan that needs a dearer share and names that stock.

## Scope and limits

- USD US-equity paper accounts, regular market sessions, whole-share DAY limit
  orders, and a maximum of 100 symbols / 100 child orders per plan.
- Unallocated weight and share-rounding residuals remain cash. No leverage,
  short positions, fractional holdings, options, or live trading are supported.
- Symbols held but outside the package's declared universe cause refusal.
  An author must explicitly retain an exiting symbol in the universe with no
  positive target weight to permit its planned sale.
- Missing, stale, future, crossed, or overly wide quotes stop planning or new
  submissions. IEX is the selected feed, not a claim of consolidated-market coverage.
  A refusal that concerns one stock begins with its symbol.
- A lost submission response is reconciled by client order ID. If its outcome
  cannot be established, the runtime stops; it never guesses that resending is safe.
  An order the broker refuses outright halts the plan instead. Once the plan's
  submission window has passed, `cancel-paper` closes a plan whose unanswered
  submission the broker still cannot find. The order is never resent.
- Package expiry or a changed edition blocks new submissions. Cancellation stays
  available even after package expiry or publisher-key revocation. After a key is
  removed from the trust file, a full snapshot signed with a trusted key replaces
  the installed edition in the same state directory; see
  [SECURITY.md](../SECURITY.md).
- No real broker orders were used to qualify this implementation. Offline tests
  exercise simulated broker outcomes and HTTP transports; they do not establish
  brokerage acceptance, fills, or strategy performance.

See [package format](PACKAGE_FORMAT.md), [operations](OPERATIONS.md), and
[boundary](BOUNDARY.md).

## Development

```sh
.venv/bin/python -m pip install -r requirements-test.lock
.venv/bin/python -m pytest -q
```

The source is MIT-licensed. Rights to an author's research are supplied separately
with that research. Publisher signatures establish origin and integrity; they do
not verify research accuracy, prove payment, or prevent independent research.
