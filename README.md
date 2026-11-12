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

## 2. What you will find here

**Catalog**
- `catalog/themes.json`: every industry and theme that has been researched,
  is being researched, or has been committed to.
- `catalog/authors.json`: every author and the public keys they sign with.
- `catalog/products/`: one entry per research product.

**Free past quarters** (`history/`)
For each product, past quarterly evaluations: the companies assessed, each
company's scores and rank, and the resulting portfolio selection and weights.
Each edition and its scores are signed by their author, so you can check where
they came from and that they are unchanged.

**Tools**
- An engine that verifies a signed research package, shows the research,
  previews a portfolio and can run it in an Alpaca paper-trading account.
- The package format specification and machine-readable schemas.
- Key generation, signing and validation commands for authors.
- Templates for a package, an evaluation and a news configuration, with a
  complete fictional example.
- An authoring guide (`docs/AUTHORING.md`).

## 3. Limits you should know

- **Paper trading only.** The engine connects to Alpaca's paper endpoint and
  has no live-trading mode.
- **Signatures show origin, not quality.** A signature proves which author
  published a package and that it has not changed. Editions are currently
  published by their authors without independent review; independent review
  will be added later and will be shown in the catalog when it exists.
- **Nothing here is investment advice.**

## 4. Current research

Current-quarter research is provided to firms that license a product. They
receive read access to a private repository for that product, with ongoing
scores, portfolio allocations and support, in the same format the public
engine reads. Licence fees go to the package's author; the platform keeps a
small share to maintain the engine and review packages. The code that produces
an author's research is not part of what is delivered.

## 5. Contributing a new theme

1. Read `docs/AUTHORING.md` and `CONTRIBUTING.md`.
2. Propose your theme by pull request to `catalog/themes.json`.
3. Generate a signing key and ask for it to be listed in `catalog/authors.json`.
4. Build, validate and sign your package with the commands in this repository.

## 6. Getting started

See `docs/ENGINE.md` to try the fictional example in a few commands, with no
account or credentials.
