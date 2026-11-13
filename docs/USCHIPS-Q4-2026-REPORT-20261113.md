# USCHIPS: Q4 2026 research sample

This free sample shows how research on government-supported industries becomes a
portfolio: **ten companies are assessed, seven receive positive target weights,
and three have exit decisions**. It covers semiconductor and clean-energy
companies exposed to the US CHIPS and Science Act and the Inflation Reduction
Act. The research compares their execution, policy support and industrial-network
position, then applies explicit selection and weighting rules.

You can read the analysis here or use the public engine to inspect the signed
research and preview a fictional account. **This is an offline demo. It cannot
place paper or live orders and is not an investment recommendation.**

## What this sample represents

The sample presents the recorded Q4 2026 research, revision 4. Its scores,
decisions and weights are fixed outputs of that research. They are model targets,
not a statement of current account holdings, a record of executed trades or
evidence of investment performance.

Two dates describe the information used:

- **October 3, 2026 — analyst assessments.** The company policy judgments consider
  the following year, through October 3, 2027. They are assessments made against
  that earlier information boundary, not promises about future eligibility.
- **October 31, 2026, 04:34:12 UTC — scorecard observations.** The financial and
  market observations used in the scorecard include disclosures after October 3.
  The resulting portfolio therefore does not represent what was knowable on
  October 3. Scores were compiled at 04:37:58 UTC on October 31.

The signed demo was published on November 12, 2026 in New York
(`2026-11-13T01:41:27.213222+00:00`). Its validity ends at midnight in New York on
January 1, 2027. **Demo status and expiry are different:** the edition cannot trade
even before that deadline, and remains available for reading and offline previews
afterwards.

This reading version was prepared on November 13, 2026. It explains the existing
edition in clearer language; it does not update the research. It is an unsigned
companion to the [original signed report](../history/uschips/2026-Q4/REPORT.md).
The publication identifiers and verification commands appear below.

## Companies and policy exposure

The universe contains six semiconductor companies and four clean-energy
companies. “US” describes the policies being studied, not every issuer's domicile
or the location of all its business.

| Sector | Companies | Policy exposure considered |
| --- | --- | --- |
| Semiconductors | GlobalFoundries (GFS), Intel (INTC), Microchip Technology (MCHP), Micron Technology (MU), Taiwan Semiconductor Manufacturing Company (TSM), Texas Instruments (TXN) | CHIPS-related direct support, research programmes and investment tax credits, with different instruments and conditions for each company |
| Clean energy | First Solar (FSLR), GE Vernova (GEV), NextEra Energy (NEE), Plug Power (PLUG) | Manufacturing and energy tax credits and relevant government-backed financing |

Programme exposure does not establish that an award was finalized, that funds
were received or that every condition was met. Grant ceilings, loan principal,
tax credits and cash receipts are different quantities. In particular,
Microchip's investment-credit exposure should not be read as a finalized direct
CHIPS grant.

## Results: scores, decisions and weights

Scores are normalized between zero and one. The composite determines selection;
it does not directly determine position size. Weights below are rounded to two
decimal places. The signed snapshot retains the exact decimal targets.

| Rank | Symbol | P1: execution | P2: policy | P3: network | Composite | Decision | Target weight |
| ---: | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | TSM | 0.6830 | 0.9907 | 0.4610 | 0.7773 | Include | 15.83% |
| 2 | MU | 0.6674 | 0.9809 | 0.3120 | 0.7175 | Include | 10.71% |
| 3 | TXN | 0.6059 | 0.9207 | 0.3490 | 0.6876 | Include | 11.98% |
| 4 | INTC | 0.4274 | 0.9896 | 0.3860 | 0.6496 | Include | 13.26% |
| 5 | GFS | 0.4724 | 0.9293 | 0.3120 | 0.6263 | Include | 10.71% |
| 6 | GEV | 0.6976 | 0.5900 | 0.2750 | 0.5540 | Include | 17.57% |
| 7 | FSLR | 0.5668 | 0.5900 | 0.3120 | 0.5302 | Include | 19.93% |
| 8 | NEE | 0.4744 | 0.5900 | 0.3870 | 0.5203 | Exit | 0.00% |
| 9 | MCHP | 0.4569 | 0.5900 | 0.2750 | 0.4847 | Exit | 0.00% |
| 10 | PLUG | 0.3968 | 0.2950 | 0.2750 | 0.3306 | Exit | 0.00% |

MCHP, NEE and PLUG fall below the **0.522775 exit threshold**. They remain in the
research universe with zero target weight. An exit describes the model's
allocation decision; it does not prove that an account sold shares or authorize
a short position.

The seven positive targets allocate **62.5% to semiconductors and 37.5% to clean
energy**. First Solar's larger weight than TSM's, despite its lower composite,
illustrates the distinction between selection and allocation: surviving companies
share a sector budget according to their network scores.

## How the method works

The sample uses method version **0.3.2**, with three pillars:

| Pillar | What it measures |
| --- | --- |
| **P1 — Execution** | Subsidy utilization, return on invested capital relative to the cost of capital, capital-expenditure execution, analyst-consensus narrative, governance and political-economy exposure |
| **P2 — Policy support** | The type and scale or materiality of eligible support, adjusted for the analyst's assessment of policy impairment |
| **P3 — Industrial network** | Industrial-network position (60%) and innovation spillovers (40%) |

Within P1, the six components have weights of 25%, 25%, 20%, 12%, 10% and 8%,
respectively. Several components use neutral assumptions, explained below.

For this scorecard, the composite is approximately:

`(P1 + 0.01)^0.321727 × (P2 + 0.01)^0.499913 × (P3 + 0.01)^0.178360`

The result is bounded to zero through one and rounded to four decimal places;
components and pillars also use four-decimal rounding. The exponents shown here
are rounded for readability. Their values reflect one quarter since the model's
inception. This multiplicative calculation explains why the composite is not a
simple weighted average of the three displayed pillars.

Selection uses all ten companies. Scores below the lower quartile exit. Re-entry
requires a score strictly above the median, **0.59015**, for two consecutive
quarters; this edition records no re-entries. Its upper-quartile flags do not add
an overweight bonus.

The surviving companies receive P3-proportional weights within their sector
budgets. Positions are constrained to between 0.5 and 1.5 times equal weight
within a sector, with a 35% portfolio-wide cap per company. Neither constraint
changes this edition's seven targets. These rules describe the published
allocation; no scores or weights have been recalculated for this reading version.

## Company assessments and evidence

The policy assessments summarized here retain the **October 3 analyst boundary**.
“No material impairment identified” is a bounded research judgment, not a claim
of zero risk or guaranteed funding. The cited documents are drawn from the
[dated evidence supplement](USCHIPS-Q4-2026-EVIDENCE-20261112.md), which gives
publication dates, SEC accessions, sections and limitations. That supplement
distinguishes retained research inputs from corroboration added later. Its
coverage is selective and does not independently substantiate every score.

### TSM — included

TSM has the highest composite score. The original assessment found no material
impairment of the eligible support considered. Its [2025 annual report](https://www.sec.gov/Archives/edgar/data/1046179/000162828026025362/tsm-20251231.htm)
describes conditional direct funding and separate government loan agreements for
TSMC Arizona. Those instruments remain distinct: loan limits are not grant
income, and the agreements do not establish that every milestone or draw has
been completed. The scorecard's ROIC uses a separate native-currency calculation.

### MU — included

Micron combines a high execution score with substantial policy support. Its
[May-quarter filing](https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/mu-20260528.htm)
describes executed funding agreements and an environmental-approval challenge.
The [July construction update](https://investors.micron.com/news/press-release/2026/Micron-Accelerates-U-S--Investments-Pours-First-Concrete-at-New-York-Fab/default.aspx)
reports progress at the New York site. The assessment found no material
impairment established by the reviewed record, while recognizing that adverse
legal outcomes or missed conditions could affect funding. Construction progress
does not certify every permit or private milestone.

### TXN — included

Texas Instruments scores above the exit threshold across the combined pillars.
Its [June-quarter filing](https://www.sec.gov/Archives/edgar/data/97476/000009747626000152/txn-20260630.htm)
separately reports CHIPS incentive proceeds and investment tax credits used
against tax payable. The original policy assessment identified no material loss
of the eligible benefits. Those reported receipts support existing benefits;
they do not guarantee all future payments. Later October financial observations
belong to the scorecard's financial record, not the earlier policy assessment.

### INTC — included

Intel's high policy-support score contributes to its inclusion despite a lower
execution pillar. The [June-quarter filing](https://www.sec.gov/Archives/edgar/data/50863/000005086326000157/intc-20260627.htm)
describes litigation concerning its government agreement and the related
procedural motions. The assessment distinguished a pending challenge from an
adverse judgment and found no material impairment established by the reviewed
facts. It did not conclude that the litigation had ended or that clawback risk
was zero.

### GFS — included

GlobalFoundries' policy-support score helps it pass the selection threshold.
Its [annual report](https://www.sec.gov/Archives/edgar/data/1709048/000170904826000022/gfs-20251231.htm)
documents commercial CHIPS funding, while its [June interim statements](https://www.sec.gov/Archives/edgar/data/1709048/000170904826000219/gfs-20260630_d2.htm)
separately disclose the continuing EDB loan. The original assessment identified
no material withdrawal of the benefits considered. Ordinary amortization is
not termination, and financing is not counted as an additional cash grant.
These selected references do not substantiate every award in the research's
aggregate registry, including its separate September R&D scope.

### GEV — included

GE Vernova's execution score places it above the exit threshold in this edition.
Its [annual report](https://www.sec.gov/Archives/edgar/data/1996810/000199681026000015/gev-20251231.htm)
recognizes wind manufacturing credits. The [IRS instructions](https://www.irs.gov/pub/irs-prior/i7207--2025.pdf)
put the specified wind-component termination date after the assessment's
October 3, 2027 horizon. Other eligibility restrictions can apply earlier, so
this timing does not guarantee company-specific immunity. The financial score
uses a sensitive estimate of June ROIC from rounded disclosures, as described
under limitations.

### FSLR — included

First Solar is just above the exit threshold and receives the larger of the two
surviving clean-energy allocations because its network pillar is higher. Its
[June-quarter filing](https://www.sec.gov/Archives/edgar/data/1274494/000127449426000170/fslr-20260630.htm)
reports manufacturing-credit benefits and describes relevant policy
restrictions. The original assessment found no material impairment established
within its scope. That finding does not remove customer-policy risk, and a
customer contract dispute is not automatically a revocation of tax credits.

### NEE — exit

NextEra's composite, 0.5203, falls just below the exit threshold. The decision is
not a finding that its policy benefits disappeared. The [June-quarter filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000060/nee-20260630.htm)
describes management's expectation that its relevant renewable pipeline could
qualify for credits. The original assessment identified no material impairment
of that scope, while treating management's expectation as conditional and
excluding benefits of an uncompleted acquisition.

### MCHP — exit

Microchip's composite, 0.4847, is below the threshold. Its [December-quarter filing](https://www.sec.gov/Archives/edgar/data/827054/000082705426000009/mchp-20251231.htm)
supports investment-tax-credit benefits while describing uncertainty around
direct-grant negotiations. The policy assessment identified no material
impairment of the benefits it considered. That does not establish a finalized
direct CHIPS grant, and the combined score still produces an exit decision.

### PLUG — exit; material partial policy impairment

Plug has the lowest composite. Its [annual report](https://www.sec.gov/Archives/edgar/data/1093691/000110465926022286/plug-20251231x10k.htm)
describes the strategic role of a finalized DOE-backed financing facility.
The [June-quarter filing](https://www.sec.gov/Archives/edgar/data/1093691/000110465926093454/plug-20260630x10q.htm)
and [DOE notice](https://www.sec.gov/Archives/edgar/data/1093691/000110465926093454/plug-20260630xex10d5.htm)
document termination following the missed first-advance deadline. No amounts
had been drawn.

The analyst judged the loss of that financing option to be materially relevant
to the aggregate policy benefit over the assessment horizon. Management's
statement that termination alone was not expected to materially affect
near-term results or cash flows is important contrary evidence: this is not
a claim of an equivalent accounting loss. Other tax-credit channels remain
separate. The categorical **0.5 impairment input is not a 50% valuation loss**.

## Assumptions and limits

- **Neutral factors:** subsidy utilization (P1a), capex execution (P1c),
  analyst-consensus narrative (P1d) and innovation spillovers (P3b) are each 0.5
  for every company. They do not distinguish names in this sample. These values
  are scoring assumptions, not observations that half an award was spent or
  that actual capex was zero.
- **Missing ownership inputs:** the insider-ownership component is neutralized
  for GEV, GFS, INTC and TXN. No invented ownership percentage replaces the
  missing value.
- **Financial estimates:** GEV's June ROIC estimate is sensitive to rounded
  restricted cash and the invested-capital denominator. It is not a return
  earned by investors. TSM uses native-currency inputs; GFS, MU and PLUG use
  recorded analyst ROIC overrides where the standard feed was insufficient.
  The supplement traces selected financial inputs, not every adjustment.
- **Evidence coverage:** the original snapshot has an empty evidence-link
  array. Public source links were supplied separately in the evidence
  supplement. Not every network relationship, governance scalar, political
  spending aggregate, award total or override has a recovered document-to-value
  trail. Selected citations cannot prove that no adverse event existed anywhere.
- **Research provenance:** earlier approval lineage for the r4 inputs remains
  unavailable. The sample is author-published and has not undergone independent
  review. A valid signature establishes origin and unchanged content, not
  analytical accuracy.
- **Different information dates:** October 3 policy judgments and October 31
  scorecard observations have different boundaries. Neither publication of the
  demo nor this rewrite refreshes those assessments.
- **Preview assumptions:** the offline account is fictional and uses illustrative
  USD 100 prices for included companies. These are not market prices or forecasts.
  Whole-share rounding can leave cash and change realized weights. No performance
  results are claimed.

## Read and preview without credentials

Reading this report requires no installation. To inspect the signed package,
first [install the engine](SAMPLE.md#install), then run the following from the
repository root. It uses only the public catalog, signed files and fictional
account; no broker account or API keys are needed.

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

The preview reports `"offline": true` and `"orders_submitted": 0`.
`--allow-expired` keeps historical reading available after the validity deadline;
it does not grant permission to trade.

## Publication record

| Item | Value |
| --- | --- |
| Product / edition | `uschips` / `2026-Q4.r4-sample` |
| Author / purpose | `nxyziggy` / `demo` |
| Exact information cutoff | `2026-10-31T04:34:12.239389+00:00` |
| Scores computed | `2026-10-31T04:37:58.416452Z` |
| Valid until | `2027-01-01T05:00:00+00:00` |
| Snapshot payload SHA-256 | `5335cec95bbe856ff4dcfcb5d024bebd1de5c2359343c071b7801b03994a2a82` |

The [signed snapshot](../history/uschips/2026-Q4/edition.snapshot.json),
[evaluation](../history/uschips/2026-Q4/evaluation.json),
[original report](../history/uschips/2026-Q4/REPORT.md) and
[release inventory](../history/uschips/2026-Q4/release.json) remain the published
record. This companion is outside that signed inventory. Its score table and
weights reproduce that record; its shorter prose and links are an editorial
presentation, not a replacement signed edition or a new research assessment.
