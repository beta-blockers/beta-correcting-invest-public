# USMaterialsPilot: Q4 2026 free sample

This signed demo contains a **25-company research subset with 18 positive targets**, reconstructed now
using company evidence available by **October 31, 2026**. It follows the existing Materials provisional
scoring formulas with the disclosed subset change. It supports reading and fictional offline previews.
It cannot place paper orders. It is not an investment recommendation.

## What this sample represents

The company dossiers were assembled in November and included later results and governance pages.
Their original scores and weights could not simply be relabeled as October research. This edition uses
earlier disclosures, recomputes CEO tenure through October 31 and calculates new subset scores and weights.
It is **not the deployed pilot, current holdings or a portfolio operated on October 31**. The original
candidate list and provisional methodology were themselves selected after the cutoff; this retrospective
application does not establish a contemporaneous strategy record or independent validation.

- Research boundary: October 31, 2026, end of day in New York.
- Latest retained company source: October 29, 2026. The boundary excludes later evidence; it does not
  mean every company issued a new disclosure that day or that all intervening news was reviewed.
- Publication: 2026-11-13T02:23:09.619181+00:00. Reconstruction is performed at publication, not backdated.
- Valid until: January 1, 2027, 05:00 UTC. Demo restrictions apply before and after that deadline.
- Evidence dates are known at day precision and serialized as the end of that UTC day; exact release
  times are not asserted. Financial period ends are separate from source publication dates.

## Scope and the unscored companies

The signed universe is AA, ABAT, ALB, AMPX, BWXT, CBT, CENX, ELBM, ENS, FLNC, GEV, GMTL, IONR, IPX, LAC, LEU, MP, NB, NVX, PPTA, SLDP, TMQ, UAMY, ULBI, USAR.
US geography describes policy exposure, not every issuer's domicile or accounting currency. Selected
support spans Defense critical-material awards, the Bipartisan Infrastructure Law,
Inflation Reduction Act manufacturing credits, DOE nuclear-fuel programmes, and CHIPS and Science Act
awards. One selected instrument supplies each company's amount/type
factor. Grants, loans, guarantees, strategic equity and procurement ceilings are not summed together.

| Unscored name | Treatment |
| --- | --- |
| XE | Confirmed pre-cutoff board independence is missing. The [April final prospectus](https://www.sec.gov/Archives/edgar/data/2088896/000110465926049515/tm2527015-22_424b4.htm) describes an anticipated roster and expected independence review, not completed determinations. The confirmed count captured in November is excluded. No score, rank or zero-score substitute is assigned. |
| EOSE | Retains the original provisional method's unscored watchlist status. Missing financial or eligibility inputs are not reconstructed in this sample. |
| OKLO | Retains the original provisional method's unscored watchlist status. Missing financial or eligibility inputs are not reconstructed in this sample. |

These three names are outside the signed universe. Their omission is not a model-generated sell
decision, and this sample does not provide a preview for an account holding an outside-universe security.
All seven scored names that fail the initial screen remain in the universe with zero target weight.

## Changes needed for the cutoff

| Company | Reconstruction |
| --- | --- |
| ALB | Removes November 4 results and the later CGP3 milestone. Operating and policy judgments use the annual filing and earlier award/governance disclosures. |
| FLNC | Removes November 2 CEO change and November website captures. Uses Julian Nebreda from September 1, 2022, and four independent directors among twelve, reconciled from the January proxy and June/September replacements. |
| SLDP | Removes November 3 results. Uses annual disclosures and the executed DOE assistance agreement. |
| CBT | Replaces FY2026 results published November 2 with aligned FY2025 statements. The proxy documents two departing directors, and the July announcement supports the October 1 CEO/director succession: eight independent of nine. |
| AMPX | Supports FY2025 figures directly with the March 10-K. The April proxy documents Hsieh's retirement and reduction to six directors; no November website is needed. |
| LEU | Replaces September TTM disclosed in November with June TTM available August 5. The earlier annual capital denominator was nonpositive; the positive June denominator is explicitly calculated below. |
| BWXT | Removes November 2 results; retains annual financials and pre-cutoff manufacturing-contract evidence. |
| GEV | Uses April board disclosures and a dated March government-role biography. October 28 results remain eligible. |
| XE | Leaves mandatory governance unresolved and the company unscored, as described above. |

Other scored companies retain existing inputs only where their supporting sources are dated by the
boundary. Qualitative judgments are reused or reassessed now against that bounded record; their
authorship is not backdated. November market quotes are omitted. No broker or news-monitor state is used.

## Selection and weighting

The conceptual background is [MIT LEAD's three-pillar framework](https://mitleadtrades.substack.com/p/performative-beta-trap-correcting).
This link points to the current article, not a frozen October copy. The existing provisional formulas
below specify the implementation used here; later article changes are not imported.

Retrospective application of the existing provisional Materials formulas to a disclosed 25-company subset. The observation boundary is October 31, 2026; the latest retained company document is dated October 29. P1 weights P1a through P1f by 0.25, 0.25, 0.20, 0.12, 0.10 and 0.08. P3 = 0.60*P3a + 0.40*P3b. The composite is clamped to [0,1] from (P1+0.01)^0.30 * (P2+0.01)^0.55 * (P3+0.01)^0.15, using the zero-age anchor and four-decimal intermediate rounding. This is an initial screen, not a completed quarterly update. Include only composites strictly above the 25-company 25th percentile (linear interpolation), 0.5063. AA equals the threshold and is excluded. The 18 survivors receive P3-proportional weights in one sleeve, with iterative redistribution above a 35% cap. No cap binds. Targets are floored to ten decimal places, leaving 0.0000000009 cash. Equal P3 values explain repeated weights; composite rank does not size positions. The source-only calculation omits operational market-eligibility checks because no price-dependent score is active and this demo cannot trade. The report lists financial bases, scoring inputs, sources and the XE gap.

The general method evaluates quarterly and requires sustained recovery before reentry. This initial
sample fabricates no completed-quarter observations, exit history or reentries. Its exclude decisions
mean failure of this initial screen, not that a live holding was sold.

## Input treatments and limitations

- P1a subsidy utilization is 0.5 for all 25 companies. This is a scoring treatment, not an assertion that half of an award has been paid or spent.
- P1c capital-expenditure execution and P1d analyst-consensus narrative are 0.5 for every company because no approved comparable plan or consensus inputs are available. No November quote or fictional preview price enters a score.
- The insider-ownership component within P1e is 0.5 for every company. Unknown raw ownership percentages stay unknown. Missing WACC uses the inherited 0.08 assumption.
- P1f political economy is uniformly 0.5 under the provisional method. Unknown lobbying and campaign amounts are not imputed as zero. Dated government-role counts remain in the evidence but do not differentiate scores.
- P3b innovation is uniformly 0.5. Effective patent 0.5, standards 0.5 and licensing 0.1 are neutral scoring assumptions, not observed innovation measurements.
- Financial inputs are dated annual or actual trailing-twelve-month estimates from public disclosures, not current feed observations. Fiscal dates and currencies differ. Nonpositive invested capital blocks a score; it is not changed to favorable ROIC.
- ULBI has an evidenced but unsized tax credit. Its amount remains unknown; the inherited unsized support branch gives P2 0.59 before policy risk. This is not a zero-dollar award.
- The signed universe is a 25-company subset. XE is unscored for missing confirmed pre-cutoff board independence. EOSE and OKLO retain the original unscored watchlist status. None receives a fabricated composite or rank.
- The initial screen and weights are recomputed over these 25 companies, not copied from a deployed portfolio. Network counts retain the fixed 28-name disclosure search and denominator 27. No completed quarterly observations, exits or reentries are invented.
- The original universe and provisional methodology were assembled after October 31. This is a retrospective source-cutoff reconstruction, not an archived portfolio known or operated on that date. Research is author-published without independent review.

Delivery track record and strategy consistency are analyst ordinals: 0 low, 0.5 mixed, 1 high.
Substitutability is 0 low, 0.5 mixed, 1 high; policy impairment is 0 none identified, 0.5 partial,
1 unavailable. These are not reported company metrics. Policy impairment is uniformly zero under the
retained selected-instrument assessments; this is not a probability of zero risk, complete news coverage
or a guarantee of funding. LEU's selected expansion award is separate from its older operations contract.

The network proxy is a bounded public-disclosure review, not a complete private supply-chain census or
an input-output economic model. Zero means no confirmed active edge in that scope, not no customers or
suppliers. Future-delivery commitments, LOIs and ownership links are excluded. The original 28-name search
uses unique neighbors divided by 27 even though 25 names are scored. The retained active edge is BWXT's
GEV-related nuclear manufacturing arrangement. Neutral factors do not repair missing mandatory evidence.

### Numeric scoring inputs

Policy amounts are USD millions. Loans, guarantees and contract ceilings are not cash grant income.
Credit amounts are observed-period benefits, not lifetime programme values. Unknown insider ownership
uses the neutral component for every company. CEO tenure uses the last possible day when only a start
month or year is known. Raw unknown political dollar amounts remain absent.

| Symbol | ROIC | Independent/seated | Track | Consistency | CEO years | Government roles | Selected type | Amount | Policy risk | Customers | Suppliers | IO proxy | Substitution |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AA | 0.02637993 | 10/11 | 1 | 1 | 3.102049 | 0 | tax_credit | 47 | 0.0 | 0 | 0 | 0.00000000 | 1 |
| ABAT | -0.97191698 | 4/5 | 0.5 | 1 | 5.177382 | 1 | grant | 57.7 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| ALB | -0.03232227 | 10/11 | 1 | 1 | 6.529908 | 2 | grant | 90 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| AMPX | -3.49408240 | 4/6 | 0.5 | 0.5 | 0.829586 | 1 | rd_contract | 74.79317311 | 0 | 0 | 0 | 0.00000000 | 0.5 |
| BWXT | 0.12189408 | 9/10 | 1 | 1 | 9.829086 | 5 | procurement_contract | 2 | 0 | 1 | 0 | 0.03703704 | 0 |
| CBT | 0.15824169 | 8/9 | 1 | 1 | 0.082137 | 0 | grant | 50 | 0 | 0 | 0 | 0.00000000 | 0.5 |
| CENX | 0.11670481 | 5/7 | 1 | 1 | 5.333443 | 0 | tax_credit | 94.3 | 0.0 | 0 | 0 | 0.00000000 | 1 |
| ELBM | -0.33637082 | 6/7 | 0.5 | 1 | 9.664812 | 2 | grant | 20 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| ENS | 0.13953990 | 9/10 | 1 | 1 | 1.440139 | 2 | tax_credit | 158.6 | 0 | 0 | 0 | 0.00000000 | 0.5 |
| FLNC | -0.19274001 | 4/12 | 0.5 | 0.5 | 4.164357 | 2 | tax_credit | 18.9 | 0 | 0 | 0 | 0.00000000 | 0.5 |
| GEV | 0.33213687 | 8/9 | 1 | 1 | 2.502447 | 1 | procurement_contract | 2 | 0 | 0 | 1 | 0.03703704 | 0.5 |
| GMTL | -0.25569534 | 3/5 | 0.5 | 1 | 4.585994 | 0 | grant | 6.2 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| IONR | -0.04130881 | 4/6 | 0.5 | 1 | 19.168087 | 1 | guarantee | 968 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| IPX | -1.13911518 | 6/8 | 0.5 | 1 | 5.667468 | 2 | grant | 5 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| LAC | -0.03454954 | 5/7 | 0.5 | 1 | 3.000746 | 2 | loan | 1970 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| LEU | 0.04792746 | 5/7 | 0.5 | 0.5 | 2.830996 | 2 | procurement_contract | 900 | 0 | 0 | 0 | 0.00000000 | 0 |
| MP | -0.06012458 | 6/7 | 0.5 | 1 | 5.952210 | 1 | loan | 150 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| NB | -2.35950973 | 5/6 | 0.5 | 1 | 13.103623 | 2 | grant | 10 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| NVX | -0.33911812 | 4/7 | 0 | 0.5 | 1.451091 | 2 | grant | 100 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| PPTA | -0.86968667 | 8/9 | 0.5 | 1 | 2.631129 | 3 | grant | 22.4 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| SLDP | -0.25566134 | 8/10 | 0.5 | 0.5 | 3.381315 | 1 | grant | 50 | 0 | 0 | 0 | 0.00000000 | 0.5 |
| TMQ | -0.12994428 | 6/7 | 0.5 | 1 | 6.414916 | 1 | strategic_equity | 17.8 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| UAMY | -0.07644269 | 5/7 | 0.5 | 1 | 1.831660 | 2 | procurement_contract | 12 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |
| ULBI | -0.02453815 | 4/5 | 0.5 | 0.5 | 3.939848 | 1 | tax_credit | Unknown (unsized) | 0 | 0 | 0 | 0.00000000 | 0.5 |
| USAR | -0.43661350 | 4/7 | 0.5 | 1 | 0.082137 | 0 | grant | 277 | 0.0 | 0 | 0 | 0.00000000 | 0.5 |

### Financial basis

Amounts are millions in the row's currency. ROIC is operating income times one minus the tax rate,
divided by equity plus interest-bearing debt minus cash. Tax rate is tax expense / pretax income,
clamped to [0, 0.5]. The inherited 21% fallback applies only when pretax is zero or both tax components
are missing. Components are aligned to the stated period; FY estimates are not current TTM.
Evidenced zero revenue is retained, and the neutral political component does not divide by it.
Native-currency ROIC is internally aligned; unused political/revenue ratios never mix currencies.

| Symbol | Period | Currency | Operating income | Pretax | Tax expense | Equity | Debt | Cash | Revenue |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AA | FY to 2025-12-31 | USD | 184 | 1083 | -49 | 6133 | 2439 | 1597 | 12831 |
| ABAT | FY to 2026-06-30 | USD | -74.70799 | -73.379021 | 0 | 126.386111 | 0 | 49.519474 | 21.741726 |
| ALB | FY to 2025-12-31 | USD | -367.084 | -552.073 | 156.881 | 9781.461 | 3193.541 | 1618.001 | 5142.733 |
| AMPX | FY to 2025-12-31 | USD | -46.646 | -44.024 | 0 | 103.815 | 0 | 90.465 | 73.011 |
| BWXT | FY to 2025-12-31 | USD | 404.459 | 398.12 | 68.259 | 1233.012 | 2015.983 | 499.779 | 3198.425 |
| CBT | FY to 2025-09-30 | USD | 621 | 565 | 196 | 1705 | 1116 | 258 | 3713 |
| CENX | FY to 2025-12-31 | USD | 158.1 | 2.7 | -13.1 | 940.6 | 548.3 | 134.2 | 2527.9 |
| ELBM | FY to 2025-12-31 | CAD | -17.017 | -133.465 | 0 | 46.25 | 43.364 | 39.024 | 0 |
| ENS | FY to 2026-03-31 | USD | 426.4 | 347.4 | 53.8 | 1908.872 | 1112.331 | 438.675 | 3751.4 |
| FLNC | TTM to 2026-06-30 | USD | -111.423 | -95.567 | 16.474 | 431.224 | 486.204 | 339.328 | 2631.864 |
| GEV | FY to 2025-12-31 | USD | 1388 | 2828 | -2051 | 12296 | 352 | 8469 | 38068 |
| GMTL | FY to 2026-06-30 | USD | -10.528 | -10.043 | 0 | 93.633 | 0 | 52.459 | 0 |
| IONR | TTM to 2026-06-30 | USD | -8.999 | -8.077 | 0 | 276.687 | 0 | 58.84 | 0 |
| IPX | FY to 2026-06-30 | USD | -65.173846 | -66.767762 | 0 | 88.299689 | 4.158979 | 35.24422 | 0 |
| LAC | FY to 2025-12-31 | USD | -52.841 | -86.262 | 0 | 1586.649 | 511.004 | 568.226 | 0 |
| LEU | TTM to 2026-06-30 | USD | 7.4 | 47.4 | -1.1 | 845.4 | 1177.5 | 1868.5 | 473.9 |
| MP | FY to 2025-12-31 | USD | -149.374 | -117.774 | -31.9 | 1978.757 | 998.741 | 1166.011 | 224.441 |
| NB | FY to 2026-06-30 | USD | -38.309 | -50.781 | 0 | 431.24 | 0 | 415.004 | 0 |
| NVX | FY to 2025-12-31 | USD | -59.567376 | -92.699645 | 0.025542 | 161.671072 | 93.848698 | 79.865999 | 5.617119 |
| PPTA | FY to 2025-12-31 | USD | -127.957 | -100.392 | 0 | 861.301 | 0 | 714.171 | 0 |
| SLDP | FY to 2025-12-31 | USD | -100.832 | -93.483 | -0.008 | 415.704 | 0.266 | 21.607 | 17.913 |
| TMQ | FY to 2025-11-30 | USD | -9.422 | -42.241 | 0 | 124.121 | 0 | 51.613 | 0 |
| UAMY | FY to 2025-12-31 | USD | -8.458865 | -4.339526 | 0 | 140.955189 | 0.195425 | 30.49432 | 39.257708 |
| ULBI | FY to 2025-12-31 | USD | -5.902 | -8.398 | -2.447 | 130.134 | 49.651 | 9.345 | 191.159 |
| USAR | FY to 2025-12-31 | USD | -59.503 | -298.684 | -0.16 | 494.286 | 1.849 | 359.925 | 1.643 |

LEU June TTM is FY2025 + H1 2026 - H1 2025: operating income 50.2 + 11.2 - 54.0 = 7.4;
pretax 85.9 + 34.1 - 72.6 = 47.4; tax 8.1 + 7.3 - 16.5 = -1.1; revenue
448.7 + 252.8 - 227.6 = 473.9. June capital is 845.4 + 1177.5 - 1868.5 = 154.4,
excluding restricted cash. The tax benefit clamps the rate to zero. CBT's aligned FY2025 debt is
260 current + 856 long term = 1116; equity includes noncontrolling interests.

Inputs are rounded for reading where shown. The evaluation contains the final four-decimal scores and
exact ten-decimal targets. Authoring checks reproduce the unchanged provisional scorer for all 25 names
with three different positive test prices, confirming that no price assumption changes a score under
the neutral consensus treatment. Those test prices are never treated as company observations.

## Company notes and evidence

The links below support the indicated retained inputs. ROIC and revenue refer to the financial basis;
track, consistency, substitution and policy risk are bounded analyst assessments. The government-role
count remains sourced even though its scoring component is neutral. Source dates and URLs are also in
the signed snapshot. No full source captures are redistributed.

### AA

Section 45X credits are a bounded observed-period amount, not a lifetime ceiling. Composite equals 0.5063 and fails the strictly-greater initial screen.

- [Full-year2025 results](https://news.alcoa.com/press-releases/press-release-details/2026/Alcoa-Corporation-Reports-Fourth-Quarter-and-Full-Year-2025-Results/default.aspx) — 2026-01-22; supports consist, cust, io, pol_risk, rev, roic, subst, supp, track.
- [Third-quarter results](https://news.alcoa.com/press-releases/press-release-details/2026/Alcoa-Corporation-Reports-Third-Quarter-2026-Results/default.aspx) — 2026-10-15; supports consist, cust, io, pol_risk, subst, supp, track.
- [Q3 10Q Section45X benefit disclosures](https://www.sec.gov/Archives/edgar/data/1675149/000119312526437885/aa-20260930.htm) — 2026-10-29; supports enacted, pol_risk, sub_awarded, sub_type.
- [CEOappointment](https://www.sec.gov/Archives/edgar/data/1675149/000119312523240903/d331952d8k.htm) — 2023-09-25; supports tenure.
- [All11 nominees elected May6](https://www.sec.gov/Archives/edgar/data/1675149/000119312526216915/aa-20260506.htm) — 2026-05-07; supports revolve.
- [2026proxy](https://www.sec.gov/Archives/edgar/data/1675149/000119312526115997/aa-20260319.htm) — 2026-03-19; supports board, revolve.

### ABAT

The grant and annual operating losses are retained. Neutral utilization and innovation factors do not establish completed manufacturing execution.

- [FY2026 Form10-K](https://www.sec.gov/Archives/edgar/data/1576873/000149315226042497/form10-k.htm) — 2026-09-14; supports consist, cust, enacted, io, pol_risk, rev, roic, sub_awarded, sub_type, subst, supp, track.
- [FY2026 results](https://americanbatterytechnology.com/press-release/american-battery-technology-company-reports-fy-26-financial-results-delivering-407-revenue-growth-and-positive-adjusted-gross-profit/) — 2026-09-14; supports consist, pol_risk, subst, track.
- [CEOeffectiveAugust27](https://www.sec.gov/Archives/edgar/data/1576873/000149315221021498/form8-k.htm) — 2021-08-30; supports tenure.
- [Lithium refinery grant reinstatement](https://americanbatterytechnology.com/press-release/american-battery-technology-company-wins-appeal-and-has-us-department-of-energy-grant-reinstated-for-115-million-project-for-commercial-scale-critical-mineral-lithium-refinery/) — 2026-06-08; supports enacted, pol_risk, sub_awarded, sub_type.
- [2026proxy current5members](https://www.sec.gov/Archives/edgar/data/1576873/000149315226043609/formdef14a.htm) — 2026-09-22; supports board, revolve.

### ALB

Uses the February annual filing and pre-cutoff governance update. November results and the later CGP3 milestone are excluded.

- [FY2025 Form10-K](https://www.sec.gov/Archives/edgar/data/915913/000091591326000018/alb-20251231.htm) — 2026-02-11; supports consist, cust, enacted, io, pol_risk, rev, roic, sub_awarded, sub_type, subst, supp, track.
- [Independent director Bartolomeo appointment](https://www.sec.gov/Archives/edgar/data/915913/000091591326000095/alb-20260721.htm) — 2026-07-23; supports revolve.
- [Kings Mountain DPA award](https://www.albemarle.com/us/en/news/albemarle-receives-90-million-critical-materials-award-department-defense-boost-us-lithium) — 2023-09-12; supports enacted, pol_risk, sub_awarded, sub_type.
- [2026proxy](https://s201.q4cdn.com/960975307/files/doc_financials/2025/ar/ALBEMARLE-CORP_2026_Proxy_Statement.pdf) — 2026-03-24; supports board, revolve, tenure.

### AMPX

The March 10-K supports FY2025 inputs. The April proxy documents the retiring director and six-seat board; the November website is not used.

- [award](https://ir.amprius.com/sec-filings/all-sec-filings/content/0001899287-26-000065/attachment0001redacted2026.htm) — 2026-09-23; supports enacted, pol_risk, sub_awarded, sub_type.
- [ceo start](https://www.sec.gov/Archives/edgar/data/1899287/000189928726000026/ampx-20260428.htm) — 2026-04-29; supports tenure.
- [fy25 10k](https://ir.amprius.com/sec-filings/all-sec-filings/content/0001899287-26-000015/ampx-20251231.htm) — 2026-03-06; supports consist, cust, io, rev, roic, subst, supp, track.
- [proxy](https://ir.amprius.com/sec-filings/all-sec-filings/content/0001899287-26-000026/ampx-20260428.htm) — 2026-04-29; supports board, revolve.
- [q2](https://ir.amprius.com/news-events/press-releases/detail/172/amprius-technologies-reports-second-quarter-2026-financial-results-and-recent-business-highlights) — 2026-08-06; supports consist, pol_risk, subst, track.

### BWXT

Uses FY2025 and the January manufacturing agreement. November Q3 results are excluded. The BWXT-GEV active edge remains; below the initial screen.

- [bwxt gev active](https://investors.bwxt.com/news-releases/news-release-details/bwxt-awarded-historic-manufacturing-contracts-support-pickering) — 2025-01-27; supports cust, io, supp.
- [ceo start](https://www.sec.gov/Archives/edgar/data/1486957/000148695716000042/a8-kexecutivetransition.htm) — 2016-11-29; supports tenure.
- [deconversion](https://www.energy.gov/ne/articles/biden-harris-administration-announces-6-contracts-spur-americas-domestic-haleu-supply) — 2024-10-08; supports enacted, pol_risk, sub_awarded, sub_type.
- [fy25](https://investors.bwxt.com/news-releases/news-release-details/bwx-technologies-reports-fourth-quarter-and-full-year-2025) — 2026-02-23; supports consist, cust, io, pol_risk, rev, roic, subst, supp, track.
- [proxy](https://www.sec.gov/Archives/edgar/data/1486957/000148695726000021/bwxt-20260318.htm) — 2026-03-18; supports board, revolve.

### CBT

Aligned FY2025 replaces FY2026 results published November 2. The dated proxy and July announcement support the nine-seat board and October 1 succession.

- [ceo](https://investor.cabot-corp.com/news-releases/news-release-details/cabot-corporation-reports-third-quarter-fiscal-year-2026-results) — 2026-08-03; supports consist, cust, io, subst, supp, track.
- [Cabot July 30 2026: October 1 CEO and director transition](https://investor.cabot-corp.com/node/26931) — 2026-07-30; supports board, revolve, tenure.
- [doe](https://investor.cabot-corp.com/news-releases/news-release-details/cabot-corporation-expand-north-american-battery-materials) — 2026-09-17; supports consist, enacted, pol_risk, sub_awarded, sub_type, subst, track.
- [Cabot fiscal 2025 results: aligned annual financial statements](https://investor.cabot-corp.com/news-releases/news-release-details/cabot-corp-reports-fourth-quarter-and-fiscal-year-2025-results) — 2025-11-03; supports consist, cust, io, rev, roic, subst, supp, track.
- [proxy](https://www.sec.gov/Archives/edgar/data/16040/000119312526023681/d38269ddef14a.htm) — 2026-01-26; supports board, revolve.

### CENX

Section 45X uses the observed amount. High substitutability lowers P3, so the target is smaller than most selected names despite composite rank.

- [Full-year2025 results](https://www.sec.gov/Archives/edgar/data/949157/000162828026009831/exhibit99120251231q4earnin.htm) — 2026-02-19; supports consist, cust, io, pol_risk, rev, roic, subst, supp, track.
- [Second-quarter results](https://www.sec.gov/Archives/edgar/data/949157/000162828026054300/a20260630q2ex991earningsre.htm) — 2026-08-06; supports consist, cust, enacted, io, pol_risk, sub_awarded, sub_type, subst, supp, track.
- [CEO succession](https://www.sec.gov/Archives/edgar/data/949157/000094915721000085/exhibit991-pressreleaseann.htm) — 2021-05-17; supports tenure.
- [2026proxy](https://www.sec.gov/Archives/edgar/data/949157/000155278126000269/e26009_cenx-def14a.htm) — 2026-04-24; supports board, revolve.

### ELBM

The Defense grant and native-currency financial ratio retain their scope. Refinery development is not treated as completed production.

- [FY2025 annual financial statements](https://www.sec.gov/Archives/edgar/data/1907184/000117184326001993/elbm20251231_20f.htm) — 2026-03-27; supports board, consist, cust, enacted, io, pol_risk, rev, revolve, roic, sub_awarded, sub_type, subst, supp, tenure, track.
- [Second-quarter results](https://electrabmc.com/news-releases/news/electra-appoints-peter-rawlins-as-chief-financial-officer-reports-second-quarter-2026-results) — 2026-08-12; supports consist, cust, enacted, io, pol_risk, sub_awarded, sub_type, subst, supp, track.

### ENS

Uses the fiscal year ending March 31, 2026 and recorded Section 45X benefit. Annual data is not presented as a live TTM feed.

- [ceo start](https://www.sec.gov/Archives/edgar/data/1289308/000128930825000020/ens-20250523.htm) — 2025-05-23; supports tenure.
- [fy26](https://investor.enersys.com/news/news-details/2026/CORRECTING-and-REPLACING-EnerSys-Reports-Fourth-Quarter-and-Full-Year-Fiscal-2026-Results/default.aspx) — 2026-05-21; supports consist, enacted, rev, roic, sub_awarded, sub_type, subst, track.
- [fy26 original network](https://investor.enersys.com/news/news-details/2026/EnerSys-Reports-Fourth-Quarter-and-Full-Year-Fiscal-2026-Results/default.aspx) — 2026-05-20; supports cust, io, supp.
- [proxy](https://www.sec.gov/Archives/edgar/data/1289308/000119312526294512/d32071ddef14a.htm) — 2026-07-02; supports board, revolve.
- [q1](https://investor.enersys.com/news/news-details/2026/EnerSys-Reports-First-Quarter-Fiscal-2027-Results/default.aspx) — 2026-08-12; supports consist, enacted, pol_risk, sub_type, subst, track.

### FLNC

October CEO is Julian Nebreda, with tenure from September 1, 2022; board is four independent of twelve. The November CEO change and website roster are excluded. Below the initial screen.

- [board coughlin](https://www.sec.gov/Archives/edgar/data/1868941/000110465926108270/tm2625477d1_8k.htm) — 2026-09-16; supports board, consist, revolve, track.
- [Fluence June 5 2026 Form 8-K: Shelton replaced by Da Santos](https://ir.fluenceenergy.com/static-files/b60d07de-62a3-40ad-9fd1-8a3f53ec3dfc) — 2026-06-05; supports board, revolve.
- [board may](https://www.sec.gov/Archives/edgar/data/1868941/000186894126000037/flnc-20260827.htm) — 2026-09-01; supports board, revolve.
- [fy25](https://www.sec.gov/Archives/edgar/data/1868941/000186894125000081/flnc-20250930.htm) — 2025-11-25; supports consist, cust, io, rev, roic, subst, supp, track.
- [proxy](https://www.sec.gov/Archives/edgar/data/1868941/000114036126002380/ny20057461x1_def14a.htm) — 2026-01-26; supports board, revolve, tenure.
- [q3](https://www.sec.gov/Archives/edgar/data/1868941/000186894126000028/flncq3fy26earningspressrel.htm) — 2026-08-05; supports consist, rev, roic, subst, track.
- [q3 10q](https://www.sec.gov/Archives/edgar/data/1868941/000186894126000029/flnc-20260630.htm) — 2026-08-05; supports enacted, pol_risk, rev, roic, sub_awarded, sub_type.

### GEV

Uses FY2025 financials, October 28 results for qualitative context, April board disclosures and a March government-role biography. Below the initial screen.

- [bwxt gev active](https://investors.bwxt.com/news-releases/news-release-details/bwxt-awarded-historic-manufacturing-contracts-support-pickering) — 2025-01-27; supports cust, io, supp.
- [deconversion](https://www.energy.gov/ne/articles/biden-harris-administration-announces-6-contracts-spur-americas-domestic-haleu-supply) — 2024-10-08; supports enacted, pol_risk, sub_awarded, sub_type.
- [Bank of America March 23 2026 proxy: Arnold Donald government biography](https://www.sec.gov/Archives/edgar/data/70858/000119312526118929/d43888ddef14a.htm) — 2026-03-23; supports revolve.
- [fy25 10k](https://www.sec.gov/Archives/edgar/data/1996810/000199681026000015/gev-20251231.htm) — 2026-01-29; supports consist, cust, io, rev, roic, subst, supp, track.
- [proxy 2026](https://www.sec.gov/Archives/edgar/data/1996810/000199681026000049/gev-20260402.htm) — 2026-04-03; supports board, revolve, tenure.
- [q3](https://www.gevernova.com/news/ge-vernova-reports-strong-third-quarter-2026-financial-performance) — 2026-10-28; supports consist, pol_risk, subst, track.

### GMTL

Uses the existing grant classification and dated fiscal 2026 disclosures. Commercial production is not invented for the development asset.

- [FY2026 Form20-F](https://www.sec.gov/Archives/edgar/data/2039972/000110465926108373/gmtl-20260630x20f.htm) — 2026-09-17; supports board, consist, cust, enacted, io, pol_risk, rev, revolve, roic, sub_awarded, sub_type, subst, supp, tenure, track.

### IONR

The selected DOE guarantee is not grant revenue. The aligned financial ratio and actual period are preserved; development remains conditional.

- [DOEloan-guaranteeclosingannouncement](https://www.energy.gov/edf/articles/doe-announces-996-million-loan-guarantee-ioneer-rhyolite-ridge-advance-domestic) — 2025-01-17; supports sub_type.
- [Half-year report with preceding six-month comparison](https://www.sec.gov/Archives/edgar/data/1896084/000114036126032597/ef20079527_ex99-1.htm) — 2026-08-13; supports consist, cust, enacted, io, pol_risk, rev, roic, sub_awarded, subst, supp, track.
- [Transition-year annual report](https://announcements.asx.com.au/asxpdf/20260318/pdf/06xkpryx3wszh9.pdf) — 2026-03-18; supports board, consist, enacted, pol_risk, revolve, sub_awarded, sub_type, subst, tenure, track.

### IPX

Uses the selected grant and fiscal 2026 basis. Demonstration progress is not a claim of mature commercial-scale production.

- [FY2026 Form20-F](https://www.sec.gov/Archives/edgar/data/1898601/000189860126000030/ipx-20260630.htm) — 2026-09-29; supports board, consist, cust, enacted, io, pol_risk, rev, revolve, roic, sub_awarded, sub_type, subst, supp, tenure, track.

### LAC

The selected DOE loan commitment is not cash already received or a grant. Development-stage financials and construction risks remain.

- [FY2025 annual financial statements](https://www.sec.gov/Archives/edgar/data/1966983/000119312526115081/lac-20251231.htm) — 2026-03-19; supports consist, cust, enacted, io, pol_risk, rev, roic, sub_awarded, sub_type, subst, supp, track.
- [Second-quarter results](https://lithiumamericas.com/news/news-details/2026/Lithium-Americas-Reports-Second-Quarter-2026-Results/default.aspx) — 2026-08-13; supports consist, cust, enacted, io, pol_risk, sub_awarded, sub_type, subst, supp, track.
- [Seven directors elected June22](https://www.lithiumamericas.com/news/news-details/2026/Lithium-Americas-Reports-2026-Annual-Meeting-Results/default.aspx) — 2026-06-23; supports revolve.
- [2026 Part III annual amendment](https://www.sec.gov/Archives/edgar/data/1966983/000119312526193861/d432389d10ka.htm) — 2026-04-30; supports board, revolve, tenure.
- [Walker independent appointment](https://lithiumamericas.com/news/news-details/2026/Lithium-Americas-Appoints-Clayton-Walker-to-the-Board-of-Directors/default.aspx) — 2026-05-05; supports revolve.

### LEU

Actual June TTM equals FY2025 plus H1 2026 minus H1 2025. The selected July expansion award is separate from the older operations contract with uncertain options. Few operating domestic HALEU substitutes raise P3.

- [ceo start](https://www.sec.gov/Archives/edgar/data/1065059/000106505923000075/ex991vexlerceotransition.htm) — 2023-11-20; supports tenure.
- [doe](https://www.centrusenergy.com/news/centrus-signs-contract-with-department-of-energy-for-900-million-award-intends-to-transition-haleu-production-cascade-to-commercial-operation/) — 2026-07-01; supports enacted, pol_risk, sub_awarded, sub_type.
- [fy25](https://investors.centrusenergy.com/news-releases/news-release-details/centrus-reports-fourth-quarter-and-full-year-2025-results-and) — 2026-02-10; supports consist, rev, roic, subst, track.
- [leu oklo planned](https://www.centrusenergy.com/news/oklo-centrus-sign-letter-of-intent-to-purchase-nuclear-fuel-for-aurora-powerhouse-deployment-in-southern-ohio/) — 2026-06-18; supports cust, io, supp.
- [leu xe future](https://www.sec.gov/Archives/edgar/data/1065059/000162828026053897/leu-20260806.htm) — 2026-08-06; supports cust, io, supp.
- [proxy current](https://www.sec.gov/Archives/edgar/data/1065059/000162828026027241/leu-20260424.htm) — 2026-04-24; supports board, revolve.
- [Centrus August 5 2026: Q2 financial results and June balance sheet](https://www.sec.gov/Archives/edgar/data/1065059/000162828026053433/ex991-10q2026_08x05.htm) — 2026-08-05; supports consist, cust, io, pol_risk, rev, roic, subst, supp, track.

### MP

The selected Defense loan is not combined with strategic equity or price-support commitments. Mine and magnet execution remain distinct.

- [Full-year2025 results](https://investors.mpmaterials.com/investor-news/news-details/2026/MP-Materials-Reports-Fourth-Quarter-and-Full-Year-2025-Results/) — 2026-02-26; supports consist, cust, io, pol_risk, rev, roic, subst, supp, track.
- [Second-quarter results](https://mpmaterials.com/news/mp-materials-reports-second-quarter-2026-results) — 2026-08-06; supports consist, cust, enacted, io, pol_risk, sub_awarded, sub_type, subst, supp, track.
- [2022proxy CEOemployment start](https://materials.proxyvote.com/default.aspx?docHostID=503293) — 2022-04-29; supports tenure.
- [OSC confirms execution and provision of150m direct loan](https://www.defense.gov/News/Releases/Release/Article/4270722/office-of-strategic-capital-announces-first-loan-through-dod-agreement-with-mp/) — 2025-08-10; supports enacted, pol_risk, sub_awarded, sub_type.
- [DoD partnership announcement](https://mpmaterials.com/news/mp-materials-announces-transformational-public-private-partnership-with-the-department-of-defense-to-accelerate-u-s-rare-earth-magnet-independence/) — 2025-07-10; supports consist, subst, track.
- [2026proxy](https://www.sec.gov/Archives/edgar/data/1801368/000180136826000020/mp-20260423.htm) — 2026-04-24; supports board, revolve.

### NB

The grant is distinct from broader project-financing needs. Deeply negative but defined ROIC is retained, not neutralized.

- [FY2026 Form10-K](https://www.sec.gov/Archives/edgar/data/1512228/000119312526402806/nb-20260630.htm) — 2026-09-25; supports board, consist, cust, enacted, io, pol_risk, rev, revolve, roic, sub_awarded, sub_type, subst, supp, tenure, track.
- [Elk Creek DPA award](https://www.niocorp.com/u-s-department-of-defense-awards-up-to-10-million-to-niocorps-subsidiary-elk-creek-resources-corp/) — 2025-08-05; supports enacted, pol_risk, sub_awarded, sub_type.

### NVX

Existing low execution and mixed consistency ordinals remain. The selected grant is not combined with loans or treated as cash drawn.

- [FY2025 annual financial statements](https://www.sec.gov/Archives/edgar/data/1859795/000119312526072814/nvx-20251231.htm) — 2026-02-26; supports consist, cust, enacted, io, pol_risk, rev, roic, sub_awarded, sub_type, subst, supp, tenure, track.
- [Half-year2026 financial report](https://www.sec.gov/Archives/edgar/data/1859795/000119312526378825/nvx-ex99_1.htm) — 2026-08-31; supports consist, cust, enacted, io, pol_risk, revolve, sub_awarded, sub_type, subst, supp, track.
- [Governance statement current8 includingCEO; supersedes stale7text in20F](https://ir.novonixgroup.com/static-files/1fbe265a-e9e7-4cf2-a441-a26523fc85ff) — 2026-02-26; supports board, revolve.

### PPTA

The selected Defense grant is separate from proposed or conditional financing; development-stage losses remain in ROIC.

- [FY2025 annual financial statements](https://www.sec.gov/Archives/edgar/data/1526243/000110465926037403/ppta-20251231x10k.htm) — 2026-03-31; supports consist, cust, enacted, io, pol_risk, rev, roic, sub_awarded, sub_type, subst, supp, track.
- [Second-quarter10-Q](https://www.sec.gov/Archives/edgar/data/1526243/000110465926097134/ppta-20260630x10q.htm) — 2026-08-17; supports consist, cust, enacted, io, pol_risk, sub_awarded, sub_type, subst, supp, track.
- [CEO appointment](https://perpetuaresources.com/wp-content/uploads/Perpetua-Resources-Announces-Appointment-of-Mining-Veteran-Jon-Cherry-to-Succeed-Laurel-Sayer-as-CEO_March-14-2024_FINAL-2.pdf) — 2024-03-14; supports tenure.
- [2026proxy](https://www.sec.gov/Archives/edgar/data/1526243/000110465926048110/tm2611905-1_def14a.htm) — 2026-04-24; supports board, revolve.

### SLDP

November Q3 results are excluded. Annual disclosures and the executed assistance agreement support the mixed operating ordinals and selected grant.

- [board july 8k](https://www.sec.gov/Archives/edgar/data/1844862/000110465926079956/tm2619489d1_8k.htm) — 2026-07-01; supports board, revolve.
- [ceo start](https://www.sec.gov/Archives/edgar/data/1844862/000110465923066643/tm2316913d2_ex99-1.htm) — 2023-05-31; supports tenure.
- [doe](https://www.sec.gov/Archives/edgar/data/1844862/000110465926024728/tm268168d1_ex10-1.htm) — 2026-03-03; supports enacted, pol_risk, sub_awarded, sub_type.
- [fy25](https://ir.solidpowerbattery.com/investor-relations/investor-news/news-details/2026/Solid-Power-Reports-Full-Year-2025-Results/default.aspx) — 2026-02-24; supports rev, roic.
- [fy25 10k](https://www.sec.gov/Archives/edgar/data/1844862/000110465926019435/sldp-20251231x10k.htm) — 2026-02-24; supports consist, cust, io, pol_risk, rev, roic, subst, supp, track.
- [proxy](https://www.sec.gov/Archives/edgar/data/1844862/000110465926041131/tm261518-1_def14a.htm) — 2026-04-10; supports board, revolve.

### TMQ

Strategic equity uses the explicit 0.2 instrument-type factor rather than a grant score. Below the initial-screen threshold.

- [FY2025 annual financial statements](https://www.sec.gov/Archives/edgar/data/1543418/000110465926015668/tmq-20251130x10k.htm) — 2026-02-17; supports consist, cust, io, pol_risk, rev, roic, subst, supp, tenure, track.
- [Third-quarter fiscal2026 results](https://trilogymetals.com/news-and-media/news/trilogy-metals-reports-third-quarter-fiscal-2026-financial-results/) — 2026-10-02; supports consist, cust, enacted, io, pol_risk, sub_awarded, sub_type, subst, supp, track.
- [2026 seven directors election](https://www.sec.gov/Archives/edgar/data/1543418/000127956926000445/ex991.pdf) — 2026-05-14; supports revolve.
- [2026 proxy](https://www.sec.gov/Archives/edgar/data/1543418/000110465926035492/tm266290d2_def14a.htm) — 2026-03-27; supports board, revolve.

### UAMY

Procurement support uses the explicit 0.2 instrument-type factor, not the grant factor. Below the initial-screen threshold.

- [FY2025 Form10-K](https://www.sec.gov/Archives/edgar/data/101538/000110465926032049/uamy-20251231x10k.htm) — 2026-03-19; supports consist, cust, enacted, io, pol_risk, rev, roic, sub_awarded, sub_type, subst, supp, track.
- [DLA procurement announcement](https://www.sec.gov/Archives/edgar/data/101538/000165495425011011/uamy_ex991.htm) — 2025-09-23; supports enacted, pol_risk, sub_awarded, sub_type.
- [2026 proxy statement](https://materials.proxyvote.com/Approved/911549/20260415/NOMNP_631973.PDF) — 2026-04-20; supports board, revolve, tenure.

### ULBI

Confirmed unsized tax credit uses the inherited 0.59 P2 branch; no nominal award amount is invented. Below the initial screen.

- [ceo start](https://investor.ultralifecorporation.com/news-releases/news-release-details/ultralife-corporation-names-michael-e-manna-president-ceo) — 2022-11-22; supports tenure.
- [fy25](https://investor.ultralifecorporation.com/news-releases/news-release-details/ultralife-corporation-reports-fourth-quarter-results-15) — 2026-03-10; supports consist, rev, roic, subst, track.
- [proxy](https://www.sec.gov/Archives/edgar/data/875657/000143774926019134/ulbi20260528_def14a.htm) — 2026-06-02; supports board, revolve.
- [q2](https://www.sec.gov/Archives/edgar/data/875657/000143774926026432/ulbi20260630_10q.htm) — 2026-08-03; supports consist, cust, enacted, io, pol_risk, sub_type, subst, supp, track.

### USAR

The selected grant and October CEO transition are retained from dated disclosures. Development-stage assessment does not imply operating mine production.

- [FY2025 annual financial statements](https://www.sec.gov/Archives/edgar/data/1970622/000197062226000019/exhibit991-earningsrelease.htm) — 2026-03-30; supports cust, io, pol_risk, rev, roic, supp.
- [Second-quarter results](https://www.sec.gov/Archives/edgar/data/1970622/000197062226000056/exhibit991-earningsrelease.htm) — 2026-08-10; supports consist, cust, enacted, io, pol_risk, sub_awarded, sub_type, subst, supp, track.
- [Serra Verde combination completedSeptember3](https://investors.usare.com/news-releases/news-release-details/usa-rare-earth-completes-combination-serra-verde-group) — 2026-09-04; supports consist, revolve, subst, tenure, track.
- [June3annualmeeting sixdirectorselection](https://www.sec.gov/Archives/edgar/data/1970622/000197062226000045/usar-20260603.htm) — 2026-06-04; supports revolve.
- [Executive chairman and CEO transition](https://www.sec.gov/Archives/edgar/data/1970622/000121390026079440/ea029849001ex99-1.htm) — 2026-07-20; supports revolve.
- [Commerce final CHIPS agreements](https://www.nist.gov/system/files/documents/2026/06/03/CHIPS%20USAR%20Press%20Release%202026-06-03_Final%20Version.pdf) — 2026-06-03; supports enacted, pol_risk, sub_awarded, sub_type.
- [2026 proxy director independence](https://www.sec.gov/Archives/edgar/data/1970622/000121390026047155/ea0287130-01.htm) — 2026-04-23; supports board, revolve.

## Read and preview without credentials

From the repository root, after installing the public engine:

```sh
mkdir -p .state/materials-sample
public-pilot catalog trust --product usmaterials --out .state/materials-sample/trust.json
public-pilot --trust .state/materials-sample/trust.json verify-bundle history/usmaterials/2026-Q4
public-pilot --trust .state/materials-sample/trust.json verify-evaluation history/usmaterials/2026-Q4/evaluation.json --snapshot history/usmaterials/2026-Q4/edition.snapshot.json
public-pilot --state .state/materials-sample/state --trust .state/materials-sample/trust.json install history/usmaterials/2026-Q4/edition.snapshot.json --allow-expired
public-pilot --state .state/materials-sample/state --trust .state/materials-sample/trust.json preview usmaterials --offline history/usmaterials/2026-Q4/account.fixture.json --allocation 10000 --max-order 1000 --max-turnover 10000 --max-weight 0.35
```

The fixture is an invented $10,000 cash account with no holdings or open orders. Every bid and ask is an
invented $100, and tradability flags are fictional. These are neither October prices nor live broker
observations. The explicit preview allocation avoids the small default allocation rounding most
positions to zero whole shares. Whole-share rounding and the preview price collar leave more cash than
the tiny research-weight rounding residual. An offline plan is permanently non-executable.

The five signed-release files are data only: snapshot, evaluation, report, fixture and inventory.
There are no credentials, operational account identifiers, private source captures, news collector,
research-generation code or hosted automation. A signature proves author origin and integrity, not
research accuracy. This edition is author-published and has not been independently reviewed.

## Signed evaluation

The following table is rendered directly from the signed evaluation.

# Evaluation of usmaterials, edition usmaterials-2026-q4-oct31-sample

Author `nxyziggy`, scores as of 2026-10-31T23:59:59-04:00. Bound to the snapshot payload with SHA-256 `b69eb5ecba3149c48026024ac731999ea1efe4a7a95e4d2b497c21c71b4fc7b8`.

Author-published and not independently reviewed. Check the signature and binding with `public-pilot verify-evaluation`.

## Method

Materials provisional three-pillar sample, version 1.0-oct31-subset.

Retrospective application of the existing provisional Materials formulas to a disclosed 25-company subset. The observation boundary is October 31, 2026; the latest retained company document is dated October 29. P1 weights P1a through P1f by 0.25, 0.25, 0.20, 0.12, 0.10 and 0.08. P3 = 0.60\*P3a + 0.40\*P3b. The composite is clamped to \[0,1\] from (P1+0.01)^0.30 \* (P2+0.01)^0.55 \* (P3+0.01)^0.15, using the zero-age anchor and four-decimal intermediate rounding. This is an initial screen, not a completed quarterly update. Include only composites strictly above the 25-company 25th percentile (linear interpolation), 0.5063. AA equals the threshold and is excluded. The 18 survivors receive P3-proportional weights in one sleeve, with iterative redistribution above a 35% cap. No cap binds. Targets are floored to ten decimal places, leaving 0.0000000009 cash. Equal P3 values explain repeated weights; composite rank does not size positions. The source-only calculation omits operational market-eligibility checks because no price-dependent score is active and this demo cannot trade. The report lists financial bases, scoring inputs, sources and the XE gap.

| Threshold | Value |
| --- | ---: |
| initial\_include\_strictly\_above | 0.5063 |
| initial\_percentile | 25 |
| position\_cap | 0.35 |

## Companies

| Rank | Symbol | p1 | p1a | p1b | p1c | p1d | p1e | p1f | p2 | p3 | p3a | p3b | Composite | Decision | Weight |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | CBT | 0.5168 | 0.5 | 0.4456 | 0.5 | 0.5 | 0.8036 | 0.5 | 0.7708 | 0.275 | 0.125 | 0.5 | 0.5965 | `include` | 0.0555555555 |
| 2 | LAC | 0.3898 | 0.5 | 0.0 | 0.5 | 0.5 | 0.6479 | 0.5 | 0.8695 | 0.275 | 0.125 | 0.5 | 0.5863 | `include` | 0.0555555555 |
| 3 | ENS | 0.5066 | 0.5 | 0.3988 | 0.5 | 0.5 | 0.8194 | 0.5 | 0.7303 | 0.275 | 0.125 | 0.5 | 0.5759 | `include` | 0.0555555555 |
| 4 | USAR | 0.384 | 0.5 | 0.0 | 0.5 | 0.5 | 0.5901 | 0.5 | 0.8444 | 0.275 | 0.125 | 0.5 | 0.5745 | `include` | 0.0555555555 |
| 5 | ALB | 0.4122 | 0.5 | 0.0 | 0.5 | 0.5 | 0.8721 | 0.5 | 0.7959 | 0.275 | 0.125 | 0.5 | 0.568 | `include` | 0.0555555555 |
| 6 | IONR | 0.3958 | 0.5 | 0.0 | 0.5 | 0.5 | 0.7083 | 0.5 | 0.7786 | 0.275 | 0.125 | 0.5 | 0.5546 | `include` | 0.0555555555 |
| 7 | ABAT | 0.3937 | 0.5 | 0.0 | 0.5 | 0.5 | 0.6868 | 0.5 | 0.7769 | 0.275 | 0.125 | 0.5 | 0.5531 | `include` | 0.0555555555 |
| 8 | NVX | 0.3579 | 0.5 | 0.0 | 0.5 | 0.5 | 0.3288 | 0.5 | 0.8004 | 0.275 | 0.125 | 0.5 | 0.5467 | `include` | 0.0555555555 |
| 9 | MP | 0.3956 | 0.5 | 0.0 | 0.5 | 0.5 | 0.706 | 0.5 | 0.7579 | 0.275 | 0.125 | 0.5 | 0.5465 | `include` | 0.0555555555 |
| 10 | SLDP | 0.3794 | 0.5 | 0.0 | 0.5 | 0.5 | 0.5438 | 0.5 | 0.7708 | 0.275 | 0.125 | 0.5 | 0.5448 | `include` | 0.0555555555 |
| 11 | ELBM | 0.3993 | 0.5 | 0.0 | 0.5 | 0.5 | 0.7431 | 0.5 | 0.7322 | 0.275 | 0.125 | 0.5 | 0.5378 | `include` | 0.0555555555 |
| 12 | PPTA | 0.3929 | 0.5 | 0.0 | 0.5 | 0.5 | 0.6791 | 0.5 | 0.7369 | 0.275 | 0.125 | 0.5 | 0.5371 | `include` | 0.0555555555 |
| 13 | CENX | 0.4926 | 0.5 | 0.3418 | 0.5 | 0.5 | 0.8212 | 0.5 | 0.7079 | 0.2 | 0.0 | 0.5 | 0.5365 | `include` | 0.0404040404 |
| 14 | LEU | 0.4196 | 0.5 | 0.1698 | 0.5 | 0.5 | 0.5212 | 0.5 | 0.6555 | 0.35 | 0.25 | 0.5 | 0.5322 | `include` | 0.0707070707 |
| 15 | NB | 0.3992 | 0.5 | 0.0 | 0.5 | 0.5 | 0.7417 | 0.5 | 0.7041 | 0.275 | 0.125 | 0.5 | 0.5265 | `include` | 0.0555555555 |
| 16 | AMPX | 0.3742 | 0.5 | 0.0 | 0.5 | 0.5 | 0.4916 | 0.5 | 0.713 | 0.275 | 0.125 | 0.5 | 0.5201 | `include` | 0.0555555555 |
| 17 | GMTL | 0.3891 | 0.5 | 0.0 | 0.5 | 0.5 | 0.6409 | 0.5 | 0.6857 | 0.275 | 0.125 | 0.5 | 0.5151 | `include` | 0.0555555555 |
| 18 | IPX | 0.3932 | 0.5 | 0.0 | 0.5 | 0.5 | 0.6817 | 0.5 | 0.6778 | 0.275 | 0.125 | 0.5 | 0.5134 | `include` | 0.0555555555 |
| 19 | AA | 0.4378 | 0.5 | 0.1159 | 0.5 | 0.5 | 0.8378 | 0.5 | 0.6781 | 0.2 | 0.0 | 0.5 | 0.5063 | `exclude` | 0 |
| 20 | FLNC | 0.3708 | 0.5 | 0.0 | 0.5 | 0.5 | 0.4583 | 0.5 | 0.6399 | 0.275 | 0.125 | 0.5 | 0.4892 | `exclude` | 0 |
| 21 | ULBI | 0.3799 | 0.5 | 0.0 | 0.5 | 0.5 | 0.5494 | 0.5 | 0.59 | 0.275 | 0.125 | 0.5 | 0.4715 | `exclude` | 0 |
| 22 | GEV | 0.6279 | 0.5 | 0.8803 | 0.5 | 0.5 | 0.8278 | 0.5 | 0.4077 | 0.3049 | 0.1748 | 0.5 | 0.4546 | `exclude` | 0 |
| 23 | BWXT | 0.504 | 0.5 | 0.3547 | 0.5 | 0.5 | 0.9033 | 0.5 | 0.4077 | 0.3799 | 0.2998 | 0.5 | 0.44 | `exclude` | 0 |
| 24 | TMQ | 0.3961 | 0.5 | 0.0 | 0.5 | 0.5 | 0.7106 | 0.5 | 0.4874 | 0.275 | 0.125 | 0.5 | 0.4305 | `exclude` | 0 |
| 25 | UAMY | 0.3886 | 0.5 | 0.0 | 0.5 | 0.5 | 0.6362 | 0.5 | 0.4714 | 0.275 | 0.125 | 0.5 | 0.4205 | `exclude` | 0 |

## Notes

- **CBT**: Aligned FY2025 replaces FY2026 results published November 2. The dated proxy and July announcement support the nine-seat board and October 1 succession.
- **LAC**: The selected DOE loan commitment is not cash already received or a grant. Development-stage financials and construction risks remain.
- **ENS**: Uses the fiscal year ending March 31, 2026 and recorded Section 45X benefit. Annual data is not presented as a live TTM feed.
- **USAR**: The selected grant and October CEO transition are retained from dated disclosures. Development-stage assessment does not imply operating mine production.
- **ALB**: Uses the February annual filing and pre-cutoff governance update. November results and the later CGP3 milestone are excluded.
- **IONR**: The selected DOE guarantee is not grant revenue. The aligned financial ratio and actual period are preserved; development remains conditional.
- **ABAT**: The grant and annual operating losses are retained. Neutral utilization and innovation factors do not establish completed manufacturing execution.
- **NVX**: Existing low execution and mixed consistency ordinals remain. The selected grant is not combined with loans or treated as cash drawn.
- **MP**: The selected Defense loan is not combined with strategic equity or price-support commitments. Mine and magnet execution remain distinct.
- **SLDP**: November Q3 results are excluded. Annual disclosures and the executed assistance agreement support the mixed operating ordinals and selected grant.
- **ELBM**: The Defense grant and native-currency financial ratio retain their scope. Refinery development is not treated as completed production.
- **PPTA**: The selected Defense grant is separate from proposed or conditional financing; development-stage losses remain in ROIC.
- **CENX**: Section 45X uses the observed amount. High substitutability lowers P3, so the target is smaller than most selected names despite composite rank.
- **LEU**: Actual June TTM equals FY2025 plus H1 2026 minus H1 2025. The selected July expansion award is separate from the older operations contract with uncertain options. Few operating domestic HALEU substitutes raise P3.
- **NB**: The grant is distinct from broader project-financing needs. Deeply negative but defined ROIC is retained, not neutralized.
- **AMPX**: The March 10-K supports FY2025 inputs. The April proxy documents the retiring director and six-seat board; the November website is not used.
- **GMTL**: Uses the existing grant classification and dated fiscal 2026 disclosures. Commercial production is not invented for the development asset.
- **IPX**: Uses the selected grant and fiscal 2026 basis. Demonstration progress is not a claim of mature commercial-scale production.
- **AA**: Section 45X credits are a bounded observed-period amount, not a lifetime ceiling. Composite equals 0.5063 and fails the strictly-greater initial screen.
- **FLNC**: October CEO is Julian Nebreda, with tenure from September 1, 2022; board is four independent of twelve. The November CEO change and website roster are excluded. Below the initial screen.
- **ULBI**: Confirmed unsized tax credit uses the inherited 0.59 P2 branch; no nominal award amount is invented. Below the initial screen.
- **GEV**: Uses FY2025 financials, October 28 results for qualitative context, April board disclosures and a March government-role biography. Below the initial screen.
- **BWXT**: Uses FY2025 and the January manufacturing agreement. November Q3 results are excluded. The BWXT-GEV active edge remains; below the initial screen.
- **TMQ**: Strategic equity uses the explicit 0.2 instrument-type factor rather than a grant score. Below the initial-screen threshold.
- **UAMY**: Procurement support uses the explicit 0.2 instrument-type factor, not the grant factor. Below the initial-screen threshold.

## Defaults disclosed

- P1a subsidy utilization is 0.5 for all 25 companies. This is a scoring treatment, not an assertion that half of an award has been paid or spent.
- P1c capital-expenditure execution and P1d analyst-consensus narrative are 0.5 for every company because no approved comparable plan or consensus inputs are available. No November quote or fictional preview price enters a score.
- The insider-ownership component within P1e is 0.5 for every company. Unknown raw ownership percentages stay unknown. Missing WACC uses the inherited 0.08 assumption.
- P1f political economy is uniformly 0.5 under the provisional method. Unknown lobbying and campaign amounts are not imputed as zero. Dated government-role counts remain in the evidence but do not differentiate scores.
- P3b innovation is uniformly 0.5. Effective patent 0.5, standards 0.5 and licensing 0.1 are neutral scoring assumptions, not observed innovation measurements.
- Financial inputs are dated annual or actual trailing-twelve-month estimates from public disclosures, not current feed observations. Fiscal dates and currencies differ. Nonpositive invested capital blocks a score; it is not changed to favorable ROIC.
- ULBI has an evidenced but unsized tax credit. Its amount remains unknown; the inherited unsized support branch gives P2 0.59 before policy risk. This is not a zero-dollar award.
- The signed universe is a 25-company subset. XE is unscored for missing confirmed pre-cutoff board independence. EOSE and OKLO retain the original unscored watchlist status. None receives a fabricated composite or rank.
- The initial screen and weights are recomputed over these 25 companies, not copied from a deployed portfolio. Network counts retain the fixed 28-name disclosure search and denominator 27. No completed quarterly observations, exits or reentries are invented.
- The original universe and provisional methodology were assembled after October 31. This is a retrospective source-cutoff reconstruction, not an archived portfolio known or operated on that date. Research is author-published without independent review.
