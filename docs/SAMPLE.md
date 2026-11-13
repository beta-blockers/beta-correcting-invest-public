# Read and preview the free USCHIPS sample

[Read the signed Q4 2026 report](../history/uschips/2026-Q4/REPORT.md) directly on GitHub.
It covers ten companies exposed to the US CHIPS Act and Inflation Reduction
Act, with scores, inclusion or exit decisions, and seven positive target
weights. No installation or account is needed to read it.

The sample is the signed `2026-Q4.r4-sample` edition of `uschips`. It combines
analyst assessments through October 3, 2026 with the observations used in the
October 31 scorecard. The report explains the methodology, neutral factors,
estimates and evidence limitations. It is author-published and not independently
reviewed.

The report is covered by the edition's signed release inventory. The commands
below verify the report and other published edition files.

**This sample is a demo edition.** The commands below read it and preview it
offline. It was unexpired on November 12, 2026 and expires at
`2027-01-01T05:00:00+00:00`. The accompanying account and quotes are fictional;
the illustrative USD 100 prices are not market observations. Until it expires,
you can also run it in your own Alpaca paper account with a trust file that
allows paper; see the [engine guide](ENGINE.md#trade-a-demo-edition-on-paper).
The report's statement that the sample never places paper orders was written
for earlier engines.

## Install

You need Git and Python 3.11 or later on Linux or macOS. Run this block from a
directory where you want a new checkout. Installation downloads Python
dependencies; the preview commands in the next section run offline. Each block
stops on its first failure without closing your terminal.

```sh
(
  set -eu
  git clone https://github.com/beta-blockers/beta-correcting-invest-public.git
  cd beta-correcting-invest-public
  python3 --version
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.lock
  .venv/bin/python -m pip install --no-deps --no-build-isolation .
  printf 'Installation passed. Enter beta-correcting-invest-public before previewing.\n'
)
```

After a successful installation, enter the checkout with
`cd beta-correcting-invest-public`. If you already have a checkout with the
engine installed, continue below from that checkout's root. Use a Python 3.11+
interpreter if `python3 --version` reports an older version.

## Preview locally

These commands create a fresh local demo directory on each run. They build a
demo-only trust file from the catalog, verify the release and evaluation,
install the edition in historical mode, display it, and preview its weights
against the fictional account. No broker account or API keys are needed.

```sh
(
  set -eu
  mkdir -p .state
  SAMPLE_RUN="$(mktemp -d .state/uschips-sample.XXXXXX)"
  .venv/bin/public-pilot catalog trust --product uschips --out "$SAMPLE_RUN/trust.json"
  .venv/bin/public-pilot --trust "$SAMPLE_RUN/trust.json" verify-bundle history/uschips/2026-Q4
  .venv/bin/public-pilot --trust "$SAMPLE_RUN/trust.json" verify history/uschips/2026-Q4/edition.snapshot.json --allow-expired
  .venv/bin/public-pilot --trust "$SAMPLE_RUN/trust.json" verify-evaluation history/uschips/2026-Q4/evaluation.json --snapshot history/uschips/2026-Q4/edition.snapshot.json
  .venv/bin/public-pilot --state "$SAMPLE_RUN/state" --trust "$SAMPLE_RUN/trust.json" install history/uschips/2026-Q4/edition.snapshot.json --allow-expired
  .venv/bin/public-pilot --state "$SAMPLE_RUN/state" --trust "$SAMPLE_RUN/trust.json" show uschips
  .venv/bin/public-pilot --state "$SAMPLE_RUN/state" --trust "$SAMPLE_RUN/trust.json" preview uschips --offline history/uschips/2026-Q4/account.fixture.json
  printf 'Sample verification and offline preview passed.\n'
)
```

The verification commands report `"status": "verified"`; snapshot verification
prints the snapshot payload's `sha256`. The final preview
contains `"offline": true` inside its plan and `"orders_submitted": 0`.
The plan shows whole-share positions, illustrative limit orders and the local
plan ID. Share rounding leaves some of the fictional account in cash.

`--allow-expired` keeps this walkthrough usable after the edition expires.
`expired` describes the edition's date validity; it does not grant trading
permission. The offline plan can never execute, whether `expired` is `true`
or `false`.

## Inspect the report and published files

- [Signed report](../history/uschips/2026-Q4/REPORT.md): the unchanged
  report covered by the edition's release inventory.
- [Signed snapshot](../history/uschips/2026-Q4/edition.snapshot.json): the
  universe, target weights, research text, dates and demo purpose.
- [Signed evaluation](../history/uschips/2026-Q4/evaluation.json): scores,
  ranks and decisions bound to the snapshot.
- [Release inventory](../history/uschips/2026-Q4/release.json): signed hashes
  for the report, snapshot, evaluation and fictional account fixture.
- [All public editions](../history/INDEX.md): the catalog's history index.

Signatures establish authorship and unchanged content. The report's limitations
remain part of the sample; verification does not establish research accuracy.
