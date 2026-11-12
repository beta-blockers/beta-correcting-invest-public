# What is public, what is licensed, what stays private

The project has three parts. Only the first is in this repository.

## 1. Public: the engine and the author kit

This repository is public and MIT-licensed. It contains:

- the engine, which verifies signed research packages, shows their research,
  previews a portfolio and runs it in an Alpaca **paper** account;
- the package format, its JSON Schemas, and the signed evaluation and release
  documents that accompany an edition;
- the author kit: key generation, validation and signing commands, templates,
  and a configuration template for the news addon;
- the catalog of themes, authors, author public keys and products;
- free past quarters under `history/`, each signed by its author;
- fictional examples and offline tests.

Everything an author needs to publish a compatible package is here. Authors
share only the package format with the platform; they keep their research
methods and code.

## 2. Licensed: current research and the news addon

Firms that license a product receive read access to a private delivery
repository for that product and quarter. A delivery contains:

- the current signed editions, evaluations and reports, in the format this
  engine reads;
- the news addon, which adjusts when rebalances are triggered between
  editions. Its code ships to licensees as part of the delivery. This
  repository carries only its configuration template
  (`author-kit/news-config.template.json`).

Licence fees go to the package's author; the platform keeps a small share for
maintaining the engine and reviewing packages. This repository contains no
payment, entitlement or licence-server code. A signature is not DRM and does
not prove payment.

## 3. Private: research production

The code that produces an author's research is never shared, with licensees or
publicly. That includes company discovery, policy and financial collectors,
source-specific normalization, research prompts and model orchestration,
scoring formulas, universe construction, target-weight production, reviewer
workspaces, evidence archives, signing keys, account configuration, broker and
cloud credentials, operational logs and unpublished research.

## Rules that keep the boundary

- Research packages and history directories are data only. They contain no
  executable code, archives, or network directives, and the engine never
  fetches evidence URLs.
- Every edition is signed by its author. Editions are currently
  author-published and **not yet independently reviewed**; the catalog will
  show review once it exists.
- This repository is published from an export of the tracked files of one
  reviewed commit, without the history of any private repository and without
  any untracked or ignored file.
- Private keys never enter a Git checkout. `scripts/export_scan.sh` rejects
  files outside an allowlist, key material, cloud identifiers and email
  addresses other than GitHub noreply addresses.
