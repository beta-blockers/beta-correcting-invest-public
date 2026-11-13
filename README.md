# Community research repository for beta-correcting portfolios

## 1. What this is for

Governments support companies through grants, tax credits, loans and
industrial programs. That support identifies a field of candidates. The idea
behind "beta-correcting" portfolios, described in
[MIT LEAD's Research to Trades](https://substack.com/home/post/p-193383265),
is to make those companies compete for passive investment on evidence of
execution: which of them put public support to productive use, create economic
value and strengthen the wider industrial ecosystem. Allocating capital by
those rules, consistently, is the long-term incentive the name refers to.

This repository is the public part of a community effort to extend that
research to more industries and regions. It provides a common engine that
reads research packages, the tools to write one, and an index of who is
researching what.

## 2. Try the free USMaterials sample

[Read the USMaterials Q4 2026 research report](history/usmaterials/2026-Q4/REPORT.md)
to see a 25-company subset assessed for US industrial-policy exposure in
minerals, metals, batteries and nuclear supply chains, with scores, inclusion
or exclusion decisions, and 18 positive portfolio target weights. Reading the
report needs no installation or account.

[Verify the signed files and preview the portfolio locally](history/usmaterials/2026-Q4/REPORT.md#read-and-preview-without-credentials)
after [installing the engine](docs/ENGINE.md#install), using the sample's
fictional account and quotes. This is a frozen research
demo for reading and offline previews. It cannot place Alpaca paper orders,
even before its expiry date.

[Inspect the dated company evidence](history/usmaterials/2026-Q4/REPORT.md#company-notes-and-evidence)
and [input treatments and limitations](history/usmaterials/2026-Q4/REPORT.md#input-treatments-and-limitations).
The sample is a retrospective reconstruction using evidence available by
October 31, 2026. The report discloses its neutral factors and unscored names.

## 3. What you will find here

**Catalog**
- `catalog/themes.json`: every industry and theme that has been researched,
  is being researched, or has been committed to.
- `catalog/authors.json`: every author and the public keys they sign with.
- `catalog/products/`: one entry per research product.

**Free samples and past quarters** ([index](history/INDEX.md))
For each product, published quarterly evaluations: the companies assessed, each
company's scores and rank, and the resulting portfolio selection and weights.
Each edition and its scores are signed by their author, so you can check where
they came from and that they are unchanged.

The [signed USCHIPS sample report](history/uschips/2026-Q4/REPORT.md) and
[offline walkthrough](docs/SAMPLE.md) are also available.

**Tools**
- An engine that verifies a signed research package, shows the research,
  previews a portfolio and can run it in an Alpaca paper-trading account.
- The package format specification and machine-readable schemas.
- Key generation, signing and validation commands for authors.
- Templates for a package, an evaluation and a news configuration, with a
  complete fictional example.
- An [authoring guide](docs/AUTHORING.md).

## 4. Limits you should know

- **Paper trading only.** The engine connects to Alpaca's paper endpoint and
  has no live-trading mode.
- **Signatures show origin, not quality.** A signature proves which author
  published a package and that it has not changed. Editions are currently
  published by their authors without independent review; independent review
  will be added later and will be shown in the catalog when it exists.
- **Nothing here is investment advice.**

## 5. Current research

**Paid research deliveries are in preparation; no signed paid release is
available yet.** Public samples are available for reading and offline previews.
A catalog listing does not announce a paid release or start a subscription.

When a signed paid release is published, firms that license it will receive
read access to its private delivery repository, with the research, updates and
support described in its release terms. Supported news and execution features
will be stated for each product; some products provide research and news only.
Licence fees will go to the package's author, with a small platform share for
maintaining the engine and reviewing packages. The code that produces an
author's research is not part of the delivery.

## 6. Contributing a new theme

Use the current `main` branch for new contributions; older feature branches may
predate the current catalog rules.

1. Read the current [authoring guide](https://github.com/beta-blockers/beta-correcting-invest-public/blob/main/docs/AUTHORING.md)
   and [contributor guide](https://github.com/beta-blockers/beta-correcting-invest-public/blob/main/CONTRIBUTING.md).
2. Generate a signing key outside every Git checkout. Only its public key and
   fingerprint belong in the repository.
3. Submit your author/key entry in `catalog/authors.json` and your theme in
   `catalog/themes.json` together in one pull request. Follow the contributor
   guide's compatibility prerequisite: until the engine rollout is complete,
   include your first product and list it in the key's `packages`; only after
   that rollout may a new author register a theme with `packages: []`.
4. Run the catalog checks before submitting. Register your first product when
   ready, if it was not included already, then build, validate and sign its
   research package as the authoring guide describes.

## 7. Getting started

Start with the [USMaterials sample walkthrough](history/usmaterials/2026-Q4/REPORT.md#read-and-preview-without-credentials) to inspect real-company
research and preview it offline. See the [engine guide](docs/ENGINE.md) for
installation, the fictional example and using a separate author-supplied paper
edition.
