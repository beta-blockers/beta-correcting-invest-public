# Scaling MIT LEAD's beta-correcting investment package into a community research repository

---

## 1. A summary of the goal of beta-correcting investment:
**The goal** of the “meritocratic beta-correcting ETFs” described in [MIT LEAD’s Research to Trades](https://substack.com/home/post/p-193383265) is to make companies compete for passive investment on evidence of execution. Government grants, tax credits, loans and industrial programs identify a field of candidates. Passive investors caring about returns for both their capital and public investments would then evaluate which companies are best putting public support to productive use, creating economic value and contributing to a wider industrial ecosystem. The proposed “beta correction” is the longer-term incentive effect of consistently allocating capital according to those rules.

**We have already provided** [an open source historical backtesting](https://github.com/nxyziggy/beta_correcting_ETFs_backtests) of automatically selected and constructed US and EU thematic portfolio, which could have respectively returned 189.52%, or 29.68% annualized and 71.38%, or 11.16% annualized, vs their respective benchmarks of 60% SOXX and 40% ICLN returning 139.63%, or 23.82% annualized and 50% EXV3.DE and 50% IQQH.DE returning 10.18%, or 1.92% annualized.

**We have also built end-to-end bots that build, trade and rebalance such portfolio with daily news and quarterly regulatory filings** for (1) US companies involved in governmental programs on critical materials, energy and infrastructure, (2) EU companies involved in renewable energy and climate, and (3) US companies receiving government money on computing and chips. These serve as demos (especially if using paper money broker account on platforms such as Alpaca, InteractiveBroker or 212Trading, all of which we built connectors for) and can also be used for personal investors wishing to allocate some of their own money into these themes. 

**To share these already built end-to-end packages** and incentivize the community to explore more industries and sector of the economies in which they hope to see better investment being channeled into, we came up with the design of such a community research repository, on which a common engine to read and process research packages produced by the community is shared, on which a pricing model will be implemented (ETF issuers or other financial institutions wishing to access or license any research package will pay directly its author, with the platform only incurring a small fee for maintenance and reviews of all research packages).


## 2. Here you will find:
**This GitHub repo here provides the public facing instruction and starter package for anyone wishing to interact with or contribute to researching a new industry previously non covered by the community.** In this repository you can find: 

- a maintained index of all industries and themes which have been researched, are being researched, or which have already been committed to being researched, in `catalog/themes.json`. `catalog/products/` lists one entry per research package already issued.-
- a maintained list of all authors and their cryptographic signatures (each industry and theme, and each evaluation package, is signed cryptographically by its author and is also peer-reviewed before publication to provide origins and guarantees of quality) at `catalog/authors.json`
- free past historic quarter evaluations for companies in each of these industries and themes, along with the scores ranked to each company and the portfolio selection and allocation weights based on said scores, at `history/`
- instructions and tutorials to run the engine, author a new package, update the documentation and index files, at `docs/`
- templates and data format examples at `examples/`

**This GitHub repo also provides the following tooling** to start reading or contributing to evaluation packages:
- An engine that verifies a signed research package, shows the research,
  previews a portfolio and can run it in an Alpaca paper-trading account.
- The package format specification and machine-readable schemas.
- Key generation, signing and validation commands for authors.
- Templates for a package, an evaluation and a news configuration, with a
  complete fictional example.
- An [authoring guide](docs/AUTHORING.md).

**Firms who pay or license research packages get Read access to private repositories whose access they bought**, which provide ongoing scoring, portfolio allocations and technical support. In these private repositories new evaluation packages are reviewed then pushed and can be read from the same public engine of the free public facing GitHub repo. A reviewer checks before approving that:
- the engine validates the package and the signature matches the listed key of the author
- the information is truthful and every evidence item resolves to a real source
- the scope matches the catalog declaration.
- no performance claim is made without valid evidence.
Research code producing the scoring, weighting and compiling source material is not shared to these firms, only ongoing research output. Author push there at every quarter a signed snapshot, report, evidence list and news configuration to their intake repository. 

**Another GitHub organization will be open only to active research contributors**, containing all research code, open issues and discussions for improvements.


## 3. Try the free USMaterials sample

[Read the USMaterials Q4 2026 research report](history/usmaterials/2026-Q4/REPORT.md)
to see a 25-company subset assessed for US industrial-policy exposure in
minerals, metals, batteries and nuclear supply chains, with scores, inclusion
or exclusion decisions, and 18 positive portfolio target weights. Reading the
report needs no installation or account.

[Verify the signed files and preview the portfolio locally](history/usmaterials/2026-Q4/REPORT.md#read-and-preview-without-credentials)
after [installing the engine](docs/ENGINE.md#install), using the sample's
fictional account and quotes. This is a frozen research
demo. Until it expires on January 1, 2027, you can also
[run it in your own Alpaca paper account](docs/ENGINE.md#trade-a-demo-edition-on-paper)
once its trust file allows paper. The report's statement that it cannot place
paper orders was written for earlier engines.

[Inspect the dated company evidence](history/usmaterials/2026-Q4/REPORT.md#company-notes-and-evidence)
and [input treatments and limitations](history/usmaterials/2026-Q4/REPORT.md#input-treatments-and-limitations).
The sample is a retrospective reconstruction using evidence available by


## 4. Limits you should know

- **Paper trading only.** The engine connects to Alpaca's paper endpoint and
  has no live-trading mode.
- **Nothing here is investment advice.**

## 5. Contributing a new theme

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

## 6. Getting started

Start with the [USMaterials sample walkthrough](history/usmaterials/2026-Q4/REPORT.md#read-and-preview-without-credentials) to inspect real-company
research and preview it offline. See the [engine guide](docs/ENGINE.md) for
installation, the fictional example and using a separate author-supplied paper
edition.
