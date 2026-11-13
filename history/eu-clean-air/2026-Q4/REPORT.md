# EU Clean Air Pilot: November 6, 2026 free sample

This free sample preserves four completed research scorecards and the initial target allocation
of the separate EU political-spending and confirmed-link variant. It is a signed **demo** for
reading and fictional offline previews. It cannot submit paper or live orders. The publication
contains no return series, trading results or claim of investment performance.

## Dates and scope

- **Evidence cutoff:** `2026-11-06T04:24:51.531890+00:00`.
- **Model treatment and allocation recorded:** `2026-11-06T04:39:01+00:00`.
- **Public sample prepared and signed:** `2026-11-13T03:05:17.401519+00:00`.
- **Demo validity ends:** January 1, 2027 at 00:00 Europe/Paris (December 31, 2026 at 23:00 UTC). This quarter-end metadata is assigned to the public demo; it is not a new claim about the private research's original expiry, nor permission to trade before that time.
- The November 5 prices and November 5–6 disclosures and observations remain part of the evidence. **This is not an October 31 sample.** Later operational work, news and broker quotes are not used to update these scores.
- Four completed eligible companies form the scored universe. The broader 15-company reference set is used only for the network analysis. EU refers to industrial-policy exposure; Nel is Norwegian.
- The relevant programs are the EU Innovation Fund and Horizon Europe. Clean-air is the research theme, not the name of a single enacted EU statute.

## Scores and recorded allocation

| Rank | Company | Research symbol | Composite | Score basis | Target weight |
| ---: | --- | --- | ---: | --- | ---: |
| 1 | Siemens Energy | ENR.DE | 0.6928 | Model-assigned | 35.0000% |
| 2 | Nel | NEL.OL | 0.5670 | Model-assigned | 30.4670% |
| 3 | Alfen | ALFEN.AS | 0.5137 | Model-assigned | 34.5330% |
| 4 | Enel | ENEL.MI | 0.4159 | Evidence-complete within selected scope | 0.0000% |

The signed evaluation retains every component, rank, threshold, decision and exact target
decimal. Enel remains in the universe with a zero target and the recorded startup `exit`
decision. The original calculation began with no holdings: that label does not describe a sale.
The three positive targets were intended to use the entire model allocation. Their serialized
decimals sum to 0.99999999999999997; the negligible decimal residual is retained, not redistributed.

P1 is company execution, P2 industrial-policy support and P3 network position. P1a–P1f are
subsidy utilization, ROIC spread, capex execution, analyst targets, governance, and political
spending/government service. P3a is network position and P3b innovation spillovers.

### How the cap produces these weights

Start with P3 normalized across the three survivors. The 0.5–1.5 times equal-weight
bounds (16.6667%–50%) do not bind here. Then clip Siemens Energy to the 35% position
cap and divide the released weight **equally** between the two remaining companies.
If another company reaches the cap, clip again and split the residual equally among
those still below it. A budget that cannot fit under the caps stays as cash.

| Company | P3 | Initial P3-normalized weight | Adjustment, percentage points | Final weight |
| --- | ---: | ---: | ---: | ---: |
| Alfen | 0.3132 | 33.33688132% | +1.19611495 | 34.53299627% |
| Siemens Energy | 0.3513 | 37.39222991% | -2.39222991 | 35.00000000% |
| Nel | 0.2750 | 29.27088877% | +1.19611495 | 30.46700373% |

The table rounds only for display. The signed targets preserve the original decimal
values. The complete two-stage redistribution rule is also in `evaluation.json`.

## Known gaps and assigned inputs

| Company | Raw campaign amount (USD millions) | ROIC input (fraction) | Campaign penalty in P1f |
| --- | ---: | ---: | ---: |
| Siemens Energy | `null` (undisclosed) | 0.9467959966831865 | 0.1 |
| Nel | `null` (undisclosed) | `null` (undisclosed) | 0.1 |
| Alfen | `null` (undisclosed) | 0.012049706542252583 | 0.1 |
| Enel | 0 | 0.06966774595939818 | Disclosed-zero input |

A point model score does not make a missing raw disclosure known. Nel's raw ROIC stays
unknown, while its entire supported interval gives the same ROIC-spread score. Enel's reported
zero campaign amount covers the parent, main Italian companies, Endesa, Enel Americas and
Enel Chile; it is not a claim about every possible political expense. All neutral factor and
analyst-assessment treatments are listed in the signed evaluation below.

### Siemens Energy: why the derived ROIC is 94.6796%

This is the strategy's **derived ROIC input**, not a ratio reported by Siemens Energy.
The income period is July 1, 2025–June 30, 2026. Amounts below are EUR millions.
TTM means FY2025 plus the first nine months of FY2026 minus the comparable nine
months of FY2025. Tax charges shown in parentheses are treated as positive expense.

| Income input | FY2025 | 9M FY2026 | 9M FY2025 | TTM |
| --- | ---: | ---: | ---: | ---: |
| Operating income | 2,149 | 3,539 | 1,866 | 3,822 |
| Pretax income | 2,213 | 3,689 | 1,913 | 3,989 |
| Tax expense | 527 | 920 | 464 | 983 |

Sources: [FY2025 annual report, physical PDF page 148](https://assets.siemens-energy.com/dam/32b27e9a-af91-4915-8b51-b3af012d0d98/A-Siemens_Energy_Annual_Report_2025-pdf_Original%20file.pdf#page=148)
and [Q3 FY2026 release, physical PDF page 9 (printed III)](https://assets.siemens-energy.com/dam/d0147174-31a9-4a78-b062-b49d00428fc4/earnings-release-q3-fy2026-en-pdf_Original%20file.pdf#page=9).

| Capital input at June 30, 2026 | EUR millions |
| --- | ---: |
| Total equity, including non-controlling interests | 11,171 |
| Current debt | 407 |
| Non-current debt | 2,552 |
| Less: cash and cash equivalents | (11,088) |
| Invested capital under this definition | **3,042** |

Source: [Q3 FY2026 release, physical PDF page 11 (printed V)](https://assets.siemens-energy.com/dam/d0147174-31a9-4a78-b062-b49d00428fc4/earnings-release-q3-fy2026-en-pdf_Original%20file.pdf#page=11).

The formula is `TTM operating income × (1 − clamp(TTM tax expense / TTM pretax
income, 0, 0.5)) / (latest total equity + current debt + non-current debt − cash)`.
Here the tax clamp does not bind: `983 / 3,989 = 24.6428%`.
After-tax operating income is `3,822 × (1 − 983 / 3,989)`, approximately `2,880.153422`.
Dividing by `3,042` gives **0.9467959966831865**, or approximately **94.6796%**.

The high ratio follows from using a small capital base after subtracting all cash.
The calculation uses the latest balance sheet, without averaging capital or adjusting
reported operating income for special items. It is therefore definition-sensitive and
cannot be treated as interchangeable with issuer ROCE or a vendor's differently
defined ROIC. The frozen ratio and the maximum P1b score of **1.0** are unchanged.

## Lobbying and network sensitivity

The following retained score intervals vary the otherwise unknown campaign amount across its
allowed penalty range (and Nel's ROIC across its supported interval). **They are sensitivity
ranges, not the selected half-penalty point scores and not return forecasts.** The low and high
columns use the two endpoints of the filed lobbying band. No weight sensitivity is claimed.

| Company | Reported period | Lobbying band, EUR | Selected midpoint, EUR | Composite at low band endpoint | Composite at high band endpoint |
| --- | --- | ---: | ---: | --- | --- |
| Siemens Energy | 10/2024 - 09/2025 | 2,000,000–2,249,999 | 2,124,999.50 | 0.6903–0.6954 | 0.6903–0.6954 |
| Nel | 01/2025 - 12/2025 | 200,000–299,999 | 249,999.50 | 0.5649–0.5717 | 0.5623–0.5692 |
| Alfen | 07/2025 - 06/2026 | 100,000–199,999 | 149,999.50 | 0.5111–0.5166 | 0.5108–0.5163 |
| Enel | 01/2025 - 12/2025 | 1,250,000–1,499,999 | 1,374,999.50 | 0.4159 | 0.4159 |

The confirmed network links are Alfen → EDF/Luminus, Siemens Energy → Orsted,
Siemens Energy → EDF/Enedis, and EDF → Enel. Each company's distinct-neighbor count uses
the other 14 reference companies as its denominator. This is a limited observed-degree proxy;
the source set does not establish complete supply-chain coverage.
A disputed reverse Enel → EDF link is excluded. Including it raises Enel's composite from
0.4159 to 0.4198 while leaving it fourth; it does not add a second distinct EDF neighbor.
The ranking in this four-company sample remains Siemens Energy, Nel, Alfen, Enel across the
retained lobbying endpoints and that disputed-link sensitivity. A broader unobserved network
could alter the middle ranks; no claim is made that missing relationships do not exist.

### The 15 reference companies

The fixed reference set was inherited from the original EU industrial-policy research
universe. It spans semiconductors, aerospace, energy and utilities. Membership defines
the network comparison boundary; it does not itself establish a supplier–customer
link, clean-air eligibility, a completed scorecard or a portfolio allocation. Only
Alfen, Enel, Nel and Siemens Energy have completed scorecards in this edition.

| Reference company | Retained research symbol | Business area (context only) |
| --- | --- | --- |
| STMicroelectronics | STMPA.PA | Semiconductors |
| Infineon Technologies | IFX.DE | Semiconductors |
| NXP Semiconductors | NXPI | Semiconductors |
| ASML Holding | ASML | Semiconductor equipment |
| ams OSRAM | AMS.SW | Semiconductors and optoelectronics |
| Airbus | AIR.PA | Aerospace |
| Safran | SAF.PA | Aerospace |
| Enel | ENEL.MI | Electricity and utilities |
| Veolia Environnement | VIE.PA | Environmental services and utilities |
| Vestas Wind Systems | VWS.CO | Wind energy |
| Ørsted | ORSTED.CO | Energy |
| Alfen | ALFEN.AS | Electrical infrastructure |
| Nel | NEL.OL | Hydrogen equipment |
| Siemens Energy | ENR.DE | Energy technology |
| EDF | EDF.PA | Electricity and utilities |

These business areas are explanatory labels, not allocation groups. The symbols
preserve reference identities; EDF's inclusion as a counterparty does not imply a
currently investable listing. For each company, the other 14 form the denominator.

## Policy and company context

- **Alfen:** the reviewed FLEXMCS beneficiary grant face is EUR 413,875. Its dated grant conversion produces USD 0.4819574375 million. The filed lobbying band is an estimated cost and is linked by the issuer to an event. Confirmed EDF/Luminus links describe the limited network scope.
- **Enel:** the TANGO grant face is EUR 99,094,516, consolidated within the group and counted once. Its dated conversion produces USD 111.23359421 million. The retained policy-risk assessment recognizes the cancelled bank-funding channel while the grant and factory remain active. This is an analyst judgment, not a guarantee of continued support.
- **Siemens Energy:** the eligible grant aggregate covers NEMO, PIVOT, MEADOW and HIPPOW and converts to USD 279.138982345 million. The recorded assessment retains PIVOT despite its delay and assigns no identified policy impairment within the selected evidence scope. It does not assert that future conditions cannot change.
- **Nel:** the reviewed CALLUNA grant face is EUR 135,339,273, converting to USD 151.9183339425 million. The supported financial interval determines the ROIC-spread score even though a precise raw ROIC remains unavailable.

Grant amounts are committed face amounts used by the model, not cash received. The conversion
rule fixes each rate at the earliest verified publication of the exact current amount. The
financial statements, public registers, grant records, issuer assessments and FX sources are
listed in the inventory. This is author-published research without independent review.

## Offline fixture and public-engine boundary

`account.fixture.json` is entirely fictional: an empty account with 1,000 cash units and
bid/ask prices of 100 for all four symbols. Its market-open and tradable flags are invented
solely to exercise the offline planner. These are not market quotes, account balances or
broker entitlements. The public engine uses a single USD-style accounting unit; this fixture
is not a EUR/NOK conversion or a valuation of the EU portfolio.
Research symbols retain their original-listing identities. This package adds no EU broker
adapter, venue mapping, market-data feed, news runner or order connection. `purpose: demo`
and catalog trust without paper permission restrict it to reading and offline previews.

From the repository root, after installing the public engine:

```sh
SAMPLE_WORK="$(mktemp -d)"
public-pilot catalog trust --product eu-clean-air --out "$SAMPLE_WORK/trust.json"
public-pilot --trust "$SAMPLE_WORK/trust.json" verify-bundle history/eu-clean-air/2026-Q4
public-pilot --trust "$SAMPLE_WORK/trust.json" verify-evaluation history/eu-clean-air/2026-Q4/evaluation.json --snapshot history/eu-clean-air/2026-Q4/edition.snapshot.json
public-pilot --state "$SAMPLE_WORK/state" --trust "$SAMPLE_WORK/trust.json" install history/eu-clean-air/2026-Q4/edition.snapshot.json --allow-expired
public-pilot --state "$SAMPLE_WORK/state" --trust "$SAMPLE_WORK/trust.json" preview eu-clean-air --offline history/eu-clean-air/2026-Q4/account.fixture.json --max-order 1000 --max-weight 0.35
```

Those commands verify or read the signed data and produce a fictional preview. They do not
connect to a broker. No credentials are required.

## Public-source inventory

These are references reviewed for the four scorecards, their policy assessments and the frozen
15-company network. A reference in this inventory does not establish that every claim in it was
admitted. No source archive or third-party article text is redistributed. Links can change after
the freeze. The dated sources below also appear in the signed payload's `evidence` list.
Register references use the official search page and the registrant name. Their capture dates
belong to the retained issuer entry, not to the navigation page; the current register may differ.
For pages without a verified first-publication date, the inventory gives the retained capture
time instead; it does not invent a publication timestamp. Their November observations are
part of the November 6 cutoff and cannot support an October 31 reconstruction.

| Reference | Publication date supported by retained metadata | First retained capture used here (UTC) |
| --- | --- | --- |
| [1. 96e597bb58d206f85397.b-cdn.net: 2022Q4 Presentation FOR PUBLICATION.pdf](<https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2023/02/2022Q4-Presentation-FOR-PUBLICATION.pdf>) | Unverified; observation only | 2026-11-06T01:26:07.496534+00:00 |
| [2. 96e597bb58d206f85397.b-cdn.net: Q4 report 2022 FOR PUBLICATION.pdf](<https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2023/02/Q4-report-2022-FOR-PUBLICATION.pdf>) | Unverified; observation only | 2026-11-06T01:26:07.155964+00:00 |
| [3. 96e597bb58d206f85397.b-cdn.net: Q4 presentation 2024.pdf](<https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2025/02/Q4-presentation-2024.pdf>) | Unverified; observation only | 2026-11-06T01:26:08.813771+00:00 |
| [4. 96e597bb58d206f85397.b-cdn.net: Q4 report 2024.pdf](<https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2025/02/Q4-report-2024.pdf>) | Unverified; observation only | 2026-11-06T01:26:08.473772+00:00 |
| [5. alfen.com: governance](<https://alfen.com/en/esg/governance>) | Unverified; observation only | 2026-11-05T23:11:15.265692+00:00 |
| [6. alfen.com: alfen shareholders appoint maarten roef as supervisory board member](<https://alfen.com/en/investor-relations/investor-relations-news/alfen-shareholders-appoint-maarten-roef-as-supervisory-board-member>) | 2026-04-07T23:59:59.999999+00:00 | 2026-11-06T01:27:55.411412+00:00 |
| [7. alfen.com: waar te koop](<https://alfen.com/nl-be/ev-oplaadpunten/waar-te-koop>) | Unverified; observation only | 2026-11-06T03:46:32.745974+00:00 |
| [8. ams-osram.com: ams osram en hy report 2026](<https://ams-osram.com/documents/d/ams-osram/ams-osram-en-hy-report-2026>) | 2026-08-04T23:59:59.999999+00:00 | 2026-11-05T23:13:45.474415+00:00 |
| [9. ams-osram.com: eng geschafts und nachhaltigkeitsbericht ams osram 2025](<https://ams-osram.com/documents/d/ams-osram/eng-geschafts-und-nachhaltigkeitsbericht-ams-osram-2025>) | 2026-03-20T23:59:59.999999+00:00 | 2026-11-05T23:31:25.383273+00:00 |
| [10. api.live.deutsche-boerse.com: single](<https://api.live.deutsche-boerse.com/v1/data/quote_box/single?isin=DE000ENER6Y0&mic=XETR>) | Unverified; observation only | 2026-11-06T01:23:11.640279+00:00 |
| [11. assets.siemens-energy.com: robert kensbock cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/08d1ce91-2c2b-456f-8d76-b440005f5c48/robert-kensbock-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:09.385850+00:00 |
| [12. assets.siemens-energy.com: 2025 11 13 Ergebnisveröffentlichung Q4 GJ25 pdf Original file.pdf](<https://assets.siemens-energy.com/dam/0eec20ae-2771-4154-ae0b-b394012eb20b/2025-11-13_Ergebnisver%C3%B6ffentlichung-Q4-GJ25-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:13:51.526529+00:00 |
| [13. assets.siemens-energy.com: cornelia schau cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/14811dbd-bfd4-4507-b1c4-b440005f4e5e/cornelia-schau-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:09.896142+00:00 |
| [14. assets.siemens-energy.com: joe kaeser cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/17b2c818-2bc9-4b66-b069-b440005f543f/joe-kaeser-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:20:26.540514+00:00 |
| [15. assets.siemens-energy.com: veronika grimm cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/1b4552fc-0ee4-4246-8f70-b440005f6098/veronika-grimm-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:20:24.899703+00:00 |
| [16. assets.siemens-energy.com: simone menne cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/1f70b7d7-0220-4679-b9ab-b440005f5e4e/simone-menne-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:10.385000+00:00 |
| [17. assets.siemens-energy.com: lundmark pekka cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/26b3d021-dca4-47a1-8fc9-b4eb009e3e16/lundmark-pekka-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:20:25.432331+00:00 |
| [18. assets.siemens-energy.com: jürgen kerner cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/29e78f28-14a8-41c3-bd6f-b440005f552f/j%C3%BCrgen-kerner-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:10.860428+00:00 |
| [19. assets.siemens-energy.com: A Siemens Energy Annual Report 2025 pdf Original file.pdf](<https://assets.siemens-energy.com/dam/32b27e9a-af91-4915-8b51-b3af012d0d98/A-Siemens_Energy_Annual_Report_2025-pdf_Original%20file.pdf>) | 2025-12-11T23:59:59.999999+00:00 | 2026-11-05T21:54:40.163464+00:00 |
| [20. assets.siemens-energy.com: manfred bäreis cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/3d4a81f8-fa8f-452b-ab34-b440005f5780/manfred-b%C3%A4reis-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:11.315233+00:00 |
| [21. assets.siemens-energy.com: nadine florian cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/485468d1-4c89-4e01-b059-b440005f5aec/nadine-florian-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:11.783999+00:00 |
| [22. assets.siemens-energy.com: geisha williams cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/534f4713-672a-4a94-bbc0-b440005f50a8/geisha-williams-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:20:25.925089+00:00 |
| [23. assets.siemens-energy.com: thomas pfann cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/63f101a7-5b11-40a1-b848-b440005f5fa0/thomas-pfann-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:12.168680+00:00 |
| [24. assets.siemens-energy.com: martin monika cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/682ec6b5-cce6-41b8-af3f-b4eb00e0d583/martin-monika-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:12.647185+00:00 |
| [25. assets.siemens-energy.com: A Siemens Energy Annual Report 2024 pdf Original file.pdf](<https://assets.siemens-energy.com/dam/6974f976-432a-4ed9-ba61-b24301167dc8/A-Siemens-Energy-Annual-Report-2024-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T21:38:45.337609+00:00 |
| [26. assets.siemens-energy.com: CMD Energy CFO Section pdf Original file.pdf](<https://assets.siemens-energy.com/dam/81ff4952-1a7c-4fc0-9d83-b03d0154735a/CMD-Energy-CFO-Section-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-06T01:26:09.663959+00:00 |
| [27. assets.siemens-energy.com: 240930 CV Veronika Grimm DE pdf Original file.pdf](<https://assets.siemens-energy.com/dam/8d3714b6-691d-4228-8536-b234008ae8ae/240930_CV_Veronika-Grimm_DE-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-06T03:50:04.095037+00:00 |
| [28. assets.siemens-energy.com: sigmar gabriel cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/9509c0fb-ddca-4c83-ab69-b440005f5d2e/sigmar-gabriel-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:20:24.286119+00:00 |
| [29. assets.siemens-energy.com: 2023 11 21 CMD CFO final pdf Original file.pdf](<https://assets.siemens-energy.com/dam/9dc1bed6-8d20-4dbb-af20-b0c100779faa/2023-11-21-CMD-CFO-final-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-06T01:26:11.421330+00:00 |
| [30. assets.siemens-energy.com: manuel bloemers cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/a572955d-de45-4484-aa7e-b440005f5886/manuel-bloemers-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:12.901786+00:00 |
| [31. assets.siemens-energy.com: 2022 11 16 Siemens Energy Q4 Earnings Release including Guidance pdf Original file.pdf](<https://assets.siemens-energy.com/dam/b0239714-af5f-4a34-82ab-b03b007d983a/2022-11-16-Siemens-Energy-Q4-Earnings-Release-including-Guidance-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:22:23.629411+00:00 |
| [32. assets.siemens-energy.com: laurence mulliez cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/b2e4f51f-04ad-41c7-bc37-b440005f5652/laurence-mulliez-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:13.290146+00:00 |
| [33. assets.siemens-energy.com: hubert lienhard cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/b33e4684-ca75-4d64-aeaf-b440005f52fa/hubert-lienhard-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:20:27.155858+00:00 |
| [34. Siemens Energy earnings release Q3 FY2026](<https://assets.siemens-energy.com/dam/d0147174-31a9-4a78-b062-b49d00428fc4/earnings-release-q3-fy2026-en-pdf_Original%20file.pdf>) | 2026-08-05T23:59:59.999999+00:00 | 2026-11-05 |
| [35. assets.siemens-energy.com: Press release New Facility pdf Original file.pdf](<https://assets.siemens-energy.com/dam/d28307ed-0fbf-4f46-a8ba-b2f300dc66c8/Press-release_New-Facility-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T21:07:25.202131+00:00 |
| [36. assets.siemens-energy.com: feiyu xu cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/dc66342a-6ec3-451e-a9a0-b440005f4f7f/feiyu-xu-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:13.654224+00:00 |
| [37. assets.siemens-energy.com: anja dotzenrath cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/ddb8bdd6-2b0f-4a50-b879-b43c00df5f3e/anja-dotzenrath-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:20:27.642371+00:00 |
| [38. assets.siemens-energy.com: Andrea Fehrmann CV EN pdf Original file.pdf](<https://assets.siemens-energy.com/dam/de1cc9b2-42e6-416a-ab33-b43c00d288a2/Andrea-Fehrmann-CV-EN-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:13.914756+00:00 |
| [39. assets.siemens-energy.com: 2023 11 15 Earnings Release Q4 FY23 EN pdf Original file.pdf](<https://assets.siemens-energy.com/dam/e0872591-2bff-46a9-833f-b0ba015a476c/2023-11-15-Earnings-Release-Q4-FY23-EN-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:22:24.383296+00:00 |
| [40. assets.siemens-energy.com: Earnings Release Q4 EN final pdf Original file.pdf](<https://assets.siemens-energy.com/dam/ed099e7a-c429-46b9-8e57-b2260127e834/Earnings-Release-Q4_EN_final-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:22:25.931050+00:00 |
| [41. assets.siemens-energy.com: günter augustat cv en pdf Original file.pdf](<https://assets.siemens-energy.com/dam/f7d0169e-757e-40fe-ac9e-b440005f51d1/g%C3%BCnter-augustat-cv-en-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:40:14.212583+00:00 |
| [42. assets.siemens-energy.com: SE Q4FY21 Earnings Release Including FY22 Guidance pdf Original file.pdf](<https://assets.siemens-energy.com/dam/fe7059df-0726-4b0f-9c5f-b03b008e5bef/SE-Q4FY21-Earnings-Release-Including-FY22-Guidance-pdf_Original%20file.pdf>) | Unverified; observation only | 2026-11-05T23:22:22.539862+00:00 |
| [43. attachment.news.eu.nasdaq.com: a298b20fa9d0d5ef61b24572e20edc56b](<https://attachment.news.eu.nasdaq.com/a298b20fa9d0d5ef61b24572e20edc56b>) | 2026-08-12T23:59:59.999999+00:00 | 2026-11-05T21:38:45.337609+00:00 |
| [44. bur.regione.veneto.it: DettaglioDecreto.aspx](<https://bur.regione.veneto.it/BurvServices/Pubblica/DettaglioDecreto.aspx?id=587661>) | 2026-07-30T23:59:59.999999+00:00 | 2026-11-06T03:46:42.471211+00:00 |
| [45. cdn.orsted.com: orsted interim financial report q3 2026.pdf](<https://cdn.orsted.com/-/media/q32026/orsted-interim-financial-report-q3-2026.pdf?hash=BF8F727EC2E6ECAB7946480D89175E26&rev=2d35d305456e45b1b9a421c86bf40a95>) | 2026-11-05T23:59:59.999999+00:00 | 2026-11-05T21:38:45.337609+00:00 |
| [46. cinea.ec.europa.eu: hippow testing tomorrows wind technology today en](<https://cinea.ec.europa.eu/featured-projects/hippow-testing-tomorrows-wind-technology-today_en>) | Unverified; observation only | 2026-11-06T04:01:02.790720+00:00 |
| [47. cinea.ec.europa.eu: nemo building europes next generation offshore wind turbines en](<https://cinea.ec.europa.eu/featured-projects/nemo-building-europes-next-generation-offshore-wind-turbines_en>) | Unverified; observation only | 2026-11-06T03:56:58.003755+00:00 |
| [48. Innovation Fund signed/terminated project register — fresh register observation](<https://climate.ec.europa.eu/areas-action/eu-funding-climate-action/innovation-fund/innovation-fund-projects_en>) | Unverified; observation only | 2026-11-05T21:28:50.608820+00:00 |
| [49. cordis.europa.eu: 101192657](<https://cordis.europa.eu/project/id/101192657>) | Unverified; observation only | 2026-11-05T21:28:50.768658+00:00 |
| [50. cordis.europa.eu: en](<https://cordis.europa.eu/project/id/101192657/en?format=json>) | Unverified; observation only | 2026-11-05T23:18:55.854814+00:00 |
| [51. data-api.ecb.europa.eu: D.USD+DKK+NOK+CHF.EUR.SP00.A](<https://data-api.ecb.europa.eu/service/data/EXR/D.USD+DKK+NOK+CHF.EUR.SP00.A?startPeriod=2024-12-01&endPeriod=2026-11-05&format=csvdata>) | Unverified; observation only | 2026-11-05T23:47:06.777158+00:00 |
| [52. data-api.ecb.europa.eu: D.USD+DKK+NOK.EUR.SP00.A](<https://data-api.ecb.europa.eu/service/data/EXR/D.USD+DKK+NOK.EUR.SP00.A?startPeriod=2026-06-30&endPeriod=2026-09-30&format=csvdata>) | Unverified; observation only | 2026-11-05T21:38:45.337609+00:00 |
| [53. data-api.ecb.europa.eu: D.USD.EUR.SP00.A](<https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2024-01-01&endPeriod=2024-12-31&format=csvdata>) | Unverified; observation only | 2026-11-06T01:27:30.579252+00:00 |
| [54. TANGO project 101051356 factsheet](<https://ec.europa.eu/assets/cinea/project_fiches/innovation_fund/101051356.pdf>) | Unverified; observation only | 2026-11-06T02:30:56.500235+00:00 |
| [55. ec.europa.eu: 101132817.pdf](<https://ec.europa.eu/assets/cinea/project_fiches/innovation_fund/101132817.pdf>) | Unverified; observation only | 2026-11-06T01:26:18.030322+00:00 |
| [56. ec.europa.eu: 101191066.pdf](<https://ec.europa.eu/assets/cinea/project_fiches/innovation_fund/101191066.pdf>) | Unverified; observation only | 2026-11-05T21:28:51.657774+00:00 |
| [57. ec.europa.eu: 101191079.pdf](<https://ec.europa.eu/assets/cinea/project_fiches/innovation_fund/101191079.pdf>) | Unverified; observation only | 2026-11-05T21:28:52.948163+00:00 |
| [58. ec.europa.eu: 101191245.pdf](<https://ec.europa.eu/assets/cinea/project_fiches/innovation_fund/101191245.pdf>) | Unverified; observation only | 2026-11-05T21:28:51.464581+00:00 |
| [59. ec.europa.eu: 101251070.pdf](<https://ec.europa.eu/assets/cinea/project_fiches/innovation_fund/101251070.pdf>) | Unverified; observation only | 2026-11-06T01:26:16.674878+00:00 |
| [60. ec.europa.eu: 2025 FTS dataset en.csv](<https://ec.europa.eu/budget/financial-transparency-system/download/2025_FTS_dataset_en.csv>) | Unverified; observation only | 2026-11-06T01:27:33.824421+00:00 |
| [61. EU Transparency Register: search Alfen](<https://transparency-register.europa.eu/search-register-or-update/search-register_en>) | Unverified; observation only | 2026-11-05T23:22:46.892415+00:00 |
| [62. EU Transparency Register: search Nel Hydrogen](<https://transparency-register.europa.eu/search-register-or-update/search-register_en>) | Unverified; observation only | 2026-11-06T01:20:35.451602+00:00 |
| [63. EU Transparency Register: search ENEL SpA](<https://transparency-register.europa.eu/search-register-or-update/search-register_en>) | Unverified; observation only | 2026-11-06T03:45:58.736142+00:00 |
| [64. EU Transparency Register: search Siemens Energy AG](<https://transparency-register.europa.eu/search-register-or-update/search-register_en>) | Unverified; observation only | 2026-11-06T01:20:34.794299+00:00 |
| [65. echanges.dila.gouv.fr: FCECO083540 20261023.pdf](<https://echanges.dila.gouv.fr/OPENDATA/AMF/ECO/2026/10/FCECO083540_20261023.pdf>) | 2026-10-23T23:59:59.999999+00:00 | 2026-11-05T23:16:28.934319+00:00 |
| [66. edf.fr.digital-report.net: 6184](<https://edf.fr.digital-report.net/en/report/6184>) | Unverified; observation only | 2026-11-06T03:40:42.790352+00:00 |
| [67. eu-assets.contentstack.com: Alfen 2022 Annual Report.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt0513fb8100e437ac/678a67110b6b4925edeaa5ed/Alfen_2022_Annual_Report.pdf>) | Unverified; observation only | 2026-11-05T23:15:31.992276+00:00 |
| [68. eu-assets.contentstack.com: Alfen 2024 FY trading update   Press Release.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt099ec3ca20a4c36c/67b5b64eb3ac03b2224170ae/Alfen_2024_FY_trading_update_-_Press_Release.pdf>) | Unverified; observation only | 2026-11-06T01:26:08.776243+00:00 |
| [69. eu-assets.contentstack.com: Alfen 2025 FY trading update   Press Release.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt14cf238e5589d189/698b7985c3f503465ab36845/Alfen_2025_FY_trading_update_-_Press_Release.pdf>) | Unverified; observation only | 2026-11-06T01:26:09.705316+00:00 |
| [70. Alfen semi-annual report 2026](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt294b839d49cfef29/6a848064257aaf412751cdca/Alfen_2026_Semi-Annual_Report.pdf>) | 2026-08-18T23:59:59.999999+00:00 | 2026-11-05 |
| [71. eu-assets.contentstack.com: Agenda and explanatory notes.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt4ce9580a8d75e43b/699da23e6c7701000809e0f9/Agenda_and_explanatory_notes.pdf>) | Unverified; observation only | 2026-11-05T21:52:35.636133+00:00 |
| [72. eu-assets.contentstack.com: Alfen 2023 FY trading update   Press Release.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt4da3dfd2313da6ca/678a673ba0c96022828f23fd/Alfen_2023_FY_trading_update_-_Press_Release.pdf>) | Unverified; observation only | 2026-11-06T01:26:07.844958+00:00 |
| [73. eu-assets.contentstack.com: Alfen Annual Report 2025.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt5a730a1862105091/698b732ef7607f82a821efe0/Alfen_Annual_Report_2025.pdf>) | 2026-02-10T23:59:59.999999+00:00 | 2026-11-05T21:28:50.768658+00:00 |
| [74. eu-assets.contentstack.com: Alfen 2023 Annual Report.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt7101c6631a26e0fb/678a67377ec96e23ad3d4e71/Alfen_2023_Annual_Report.pdf>) | Unverified; observation only | 2026-11-05T23:15:31.098648+00:00 |
| [75. eu-assets.contentstack.com: Alfen 2026 Q3 trading update   Press Release.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt7dbff7a30080a12b/6aea450312acd3341f711c8f/Alfen_2026_Q3_trading_update_-_Press_Release.pdf>) | 2026-11-04T06:00:00+00:00 | 2026-11-05T23:15:55.834118+00:00 |
| [76. eu-assets.contentstack.com: Alfen 2022 FY trading update   Press Release.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt803564604c51abcc/678a671734e7155831ec842c/Alfen_2022_FY_trading_update_-_Press_Release.pdf>) | Unverified; observation only | 2026-11-06T01:26:06.926219+00:00 |
| [77. eu-assets.contentstack.com: Alfen 2026 AGM Minutes.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt82e6f090bc8e5d0e/6a452fc13331fe36ec601d0b/Alfen_2026_AGM_Minutes.pdf>) | Unverified; observation only | 2026-11-05T23:15:24.902187+00:00 |
| [78. eu-assets.contentstack.com: Alfen 2021 Annual Report.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/blt847b2ad47d960088/678a66fe5732c59a9b9b0d7a/Alfen_2021_Annual_Report.pdf>) | Unverified; observation only | 2026-11-05T23:15:32.339190+00:00 |
| [79. eu-assets.contentstack.com: Alfen 2026 AGM Voting Result.pdf](<https://eu-assets.contentstack.com/v3/assets/blt08d332658a89f766/bltda2c460bd74dbae4/69d63fc346476491919c5674/Alfen_2026_AGM_Voting_Result.pdf>) | Unverified; observation only | 2026-11-05T23:15:25.078519+00:00 |
| [80. eur-lex.europa.eu: pdf](<https://eur-lex.europa.eu/eli/dir/2019/944/oj/eng/pdf>) | Unverified; observation only | 2026-11-06T03:42:49.711082+00:00 |
| [81. filings.xbrl.org: Safran 2025 12 31 1 FR.xhtml](<https://filings.xbrl.org/969500UIC89GT3UL7L24/2025-12-31/ESEF/FR/0/Safran-2025-12-31-1-FR/reports/Safran-2025-12-31-1-FR.xhtml>) | 2026-03-31T23:59:59.999999+00:00 | 2026-11-05T23:26:32.975976+00:00 |
| [82. hornseaproject3.co.uk: first uk blades produced for orsteds hornsea 3 offshore wind farm](<https://hornseaproject3.co.uk/news/2026/08/first-uk-blades-produced-for-orsteds-hornsea-3-offshore-wind-farm>) | 2026-09-02T23:59:59.999999+00:00 | 2026-11-05T23:16:55.431213+00:00 |
| [83. live.euronext.com: NL0012817175 XAMS](<https://live.euronext.com/en/ajax/AwlHistoricalPrice/getFullDownloadAjax/NL0012817175-XAMS?format=csv&decimal_separator=.&date_form=d/m/Y&op=&adjusted=&base100=&startdate=2026-10-27&enddate=2026-11-05>) | Unverified; observation only | 2026-11-06T00:05:45.399283+00:00 |
| [84. live.euronext.com: NO0010081235 XOSL](<https://live.euronext.com/en/ajax/AwlHistoricalPrice/getFullDownloadAjax/NO0010081235-XOSL?format=csv&decimal_separator=.&date_form=d/m/Y&op=&adjusted=&base100=&startdate=2026-10-27&enddate=2026-11-05>) | Unverified; observation only | 2026-11-06T00:05:45.808785+00:00 |
| [85. mb.cision.com: 3986683.pdf](<https://mb.cision.com/Main/115/4321888/3986683.pdf>) | 2026-03-17T23:59:59.999999+00:00 | 2026-11-05T23:15:51.145965+00:00 |
| [86. mb.cision.com: 4030875.pdf](<https://mb.cision.com/Main/115/4333244/4030875.pdf>) | 2026-04-10T23:59:59.999999+00:00 | 2026-11-05T23:15:52.106727+00:00 |
| [87. Nel ASA Q3 2026 report](<https://mb.cision.com/Public/115/4408710/8116e8027381f514.pdf>) | 2026-10-15T23:59:59.999999+00:00 | 2026-11-05 |
| [88. mediaassets.airbus.com: pm 38 919 919350 ko9v34j5cg.pdf](<https://mediaassets.airbus.com/pm_38_919_919350-ko9v34j5cg.pdf?fileName=airbus-report-of-the-board-of-directors-2025.pdf>) | 2026-02-18T23:59:59.999999+00:00 | 2026-11-05T23:24:33.240143+00:00 |
| [89. mediaassets.airbus.com: pm 38 942 942888 eyfb5ynik9.pdf](<https://mediaassets.airbus.com/pm_38_942_942888-eyfb5ynik9.pdf?fileName=airbus-nine-month-9m-2026-press-release.pdf>) | 2026-10-28T23:59:59.999999+00:00 | 2026-11-05T23:13:23.052708+00:00 |
| [90. mobile-api.live.deutsche-boerse.com: price history](<https://mobile-api.live.deutsche-boerse.com/v1/data/price_history?limit=50&offset=0&isin=DE000ENER6Y0&mic=XETR&minDate=2026-10-01&maxDate=2026-11-06>) | Unverified; observation only | 2026-11-06T01:23:11.219166+00:00 |
| [91. mst.dk: 20260320 avedoerevaerket revurdering inkl bilag.pdf](<https://mst.dk/media/th5gtkct/20260320-avedoerevaerket-revurdering-inkl-bilag.pdf>) | 2026-03-20T23:59:59.999999+00:00 | 2026-11-06T03:54:43.812416+00:00 |
| [92. nelhydrogen.com: public disclosure](<https://nelhydrogen.com/articles/in-depth/inside-heroya-nels-first-pressurized-alkaline-production-line-takes-shape/>) | Unverified; observation only | 2026-11-06T03:56:58.132088+00:00 |
| [93. nelhydrogen.com: public disclosure](<https://nelhydrogen.com/governance/>) | Unverified; observation only | 2026-11-05T23:14:06.175524+00:00 |
| [94. nelhydrogen.com: public disclosure](<https://nelhydrogen.com/press-release/nel-asa-morten-holum-appointed-new-chief-executive-officer/>) | Unverified; observation only | 2026-11-05T21:38:45.337609+00:00 |
| [95. nelhydrogen.com: public disclosure](<https://nelhydrogen.com/press-release/nel-asa-strengthens-its-industry-leadership-as-the-final-investment-decision-has-been-taken-to-industrialize-the-next-generation-pressurized-alkaline-platform/>) | Unverified; observation only | 2026-11-06T03:42:50.259012+00:00 |
| [96. nelhydrogen.com: Annual Report 2025.pdf](<https://nelhydrogen.com/wp-content/uploads/2026/02/Annual-Report-2025.pdf>) | 2026-02-26T23:59:59.999999+00:00 | 2026-11-05T21:07:21.848048+00:00 |
| [97. orsted.com: 539821393331125](<https://orsted.com/en/media/news/2021/04/539821393331125>) | 2021-04-07T23:59:59.999999+00:00 | 2026-11-06T01:38:04.936890+00:00 |
| [98. publications.jrc.ec.europa.eu: JRC139320 01.pdf](<https://publications.jrc.ec.europa.eu/repository/bitstream/JRC139320/JRC139320_01.pdf>) | Unverified; observation only | 2026-11-06T04:01:03.294760+00:00 |
| [99. publications.jrc.ec.europa.eu: JRC139320](<https://publications.jrc.ec.europa.eu/repository/handle/JRC139320>) | Unverified; observation only | 2026-11-06T04:00:59.710176+00:00 |
| [100. recht.nrw.de: public disclosure](<https://recht.nrw.de/mblnrw/2021-s324/>) | Unverified; observation only | 2026-11-06T03:47:48.819156+00:00 |
| [101. recht.nrw.de: public disclosure](<https://recht.nrw.de/mblnrw/2025-s59-4/>) | Unverified; observation only | 2026-11-06T03:47:49.346575+00:00 |
| [102. recht.nrw.de: 457 vgv 2006 30.pdf](<https://recht.nrw.de/system/files/VB_PDF/457-vgv_2006_30.pdf>) | Unverified; observation only | 2026-11-06T03:47:50.833365+00:00 |
| [103. ted.europa.eu: xml](<https://ted.europa.eu/fr/notice/103110-2026/xml>) | 2026-02-12T23:59:59.999999+00:00 | 2026-11-06T03:57:33.976613+00:00 |
| [104. via.ritzau.dk: Annual Report 2025.pdf](<https://via.ritzau.dk/ir-files/13560592/14785310/17166/Annual%20Report%202025.pdf>) | 2026-02-06T23:59:59.999999+00:00 | 2026-11-05T23:12:38.819342+00:00 |
| [105. www.alfen.com: alfen awarded with multi year framework agreement to supply substations to liander](<https://www.alfen.com/en-nl/news/alfen-awarded-with-multi-year-framework-agreement-to-supply-substations-to-liander>) | Unverified; observation only | 2026-11-06T03:39:59.596706+00:00 |
| [106. www.arera.it: 58 26](<https://www.arera.it/atti-e-provvedimenti/dettaglio/26/58-26>) | Unverified; observation only | 2026-11-06T03:42:47.218297+00:00 |
| [107. www.borsaitaliana.it: dati completi.html](<https://www.borsaitaliana.it/borsa/azioni/dati-completi.html?isin=IT0003128367&lang=en>) | Unverified; observation only | 2026-11-05T23:49:32.924997+00:00 |
| [108. www.cashmarket.deutsche-boerse.com: Introduction of the Extended Xetra Retail Service early and late trading Planned changes to the trading process valid from 1 December 2025 4793480](<https://www.cashmarket.deutsche-boerse.com/cash-en/Stay-Informed/circulars-newsletters/deutsche-boerse-circulars/Introduction-of-the-Extended-Xetra-Retail-Service-early-and-late-trading-Planned-changes-to-the-trading-process-valid-from-1-December-2025-4793480>) | 2025-11-12T23:59:59.999999+00:00 | 2026-11-06T01:23:34.801212+00:00 |
| [109. www.consultazioniburl.servizirl.it: 01310.pdf](<https://www.consultazioniburl.servizirl.it/pdf/1999/01310.pdf>) | Unverified; observation only | 2026-11-06T03:47:53.412628+00:00 |
| [110. www.edf.fr: 2026 half year results](<https://www.edf.fr/en/the-edf-group/dedicated-sections/journalists/all-press-releases/2026-half-year-results>) | 2026-07-31T23:59:59.999999+00:00 | 2026-11-06T03:57:37.229418+00:00 |
| [111. EIB project 20220497, project and promoter names](<https://www.eib.org/en/projects/all/20220497>) | Unverified; observation only | 2026-11-06T01:22:51.088318+00:00 |
| [112. EIB project 20220497, statuses of four signed tranches](<https://www.eib.org/provider-eib-plr/app/loans/item/20220497?language=EN&defaultLanguage=EN>) | Unverified; observation only | 2026-11-06T01:25:26.258186+00:00 |
| [113. www.emarketstorage.it: 20260513 183999.pdf](<https://www.emarketstorage.it/sites/default/files/comunicati/2026-05/20260513_183999.pdf>) | 2026-05-13T23:59:59.999999+00:00 | 2026-11-05T23:27:54.040365+00:00 |
| [114. www.emarketstorage.it: 20260609 185551.pdf](<https://www.emarketstorage.it/sites/default/files/comunicati/2026-06/20260609_185551.pdf>) | Unverified; observation only | 2026-11-06T03:56:58.447118+00:00 |
| [115. www.enbridge.com: Courseulles Calvados Offshore Wind Project](<https://www.enbridge.com/Projects-and-Infrastructure/Projects/Courseulles-Calvados-Offshore-Wind-Project>) | Unverified; observation only | 2026-11-06T03:46:43.117522+00:00 |
| [116. www.endesa.fr: qui sommes nous](<https://www.endesa.fr/qui-sommes-nous>) | Unverified; observation only | 2026-11-06T03:57:35.243852+00:00 |
| [117. www.enedis.fr: quelle est la difference entre edf et enedis](<https://www.enedis.fr/faq/enedis/quelle-est-la-difference-entre-edf-et-enedis>) | Unverified; observation only | 2026-11-06T03:54:45.462692+00:00 |
| [118. www.enedis.fr: liste des fournisseurs delectricite](<https://www.enedis.fr/liste-des-fournisseurs-delectricite>) | Unverified; observation only | 2026-11-06T03:46:38.027304+00:00 |
| [119. www.enedis.fr: marche electricite facturation](<https://www.enedis.fr/marche-electricite-facturation>) | Unverified; observation only | 2026-11-06T03:46:39.399182+00:00 |
| [120. www.enedis.fr: enedis contribue la souverainete industrielle avec pres de 27 milliards deuros](<https://www.enedis.fr/presse/enedis-contribue-la-souverainete-industrielle-avec-pres-de-27-milliards-deuros>) | 2026-03-17T23:59:59.999999+00:00 | 2026-11-06T03:46:36.686899+00:00 |
| [121. www.enel.com: integrated annual report 2025.pdf](<https://www.enel.com/content/dam/enel-com/documenti/investitori/informazioni-finanziarie/2025/annuali/en/integrated-annual-report_2025.pdf>) | Unverified; observation only | 2026-11-05T23:15:11.628004+00:00 |
| [122. Enel half-year financial report at June 30 2026](<https://www.enel.com/content/dam/enel-com/documenti/investitori/informazioni-finanziarie/2026/interim/en/half-year-financial-report_30June2026.pdf>) | 2026-08-06T23:59:59.999999+00:00 | 2026-11-05 |
| [123. www.enel.com: Enel Strategic Plan 2023 2025.pdf](<https://www.enel.com/content/dam/enel-common/press/en/2022-november/Enel%20Strategic%20Plan%202023%202025.pdf>) | Unverified; observation only | 2026-11-06T03:44:12.179788+00:00 |
| [124. www.enel.com: Enel FY Results 2023.pdf](<https://www.enel.com/content/dam/enel-common/press/en/2024-march/Enel%20FY%20Results%202023.pdf>) | Unverified; observation only | 2026-11-06T03:44:12.821180+00:00 |
| [125. www.enel.com: Enel 2026 2028 Strategic Plan.pdf](<https://www.enel.com/content/dam/enel-common/press/en/2026-february/Enel%202026%202028%20Strategic%20Plan.pdf>) | Unverified; observation only | 2026-11-06T03:44:14.176780+00:00 |
| [126. www.enel.com: Enel results FY2025.pdf](<https://www.enel.com/content/dam/enel-common/press/en/2026-march/Enel%20results%20FY2025.pdf>) | Unverified; observation only | 2026-11-06T03:44:13.535292+00:00 |
| [127. www.enel.com: Enel Quarterly Bulletin 9M 2026 EN.pdf](<https://www.enel.com/content/dam/enel-common/press/en/2026-october/Enel-Quarterly-Bulletin-9M-2026_EN.pdf>) | 2026-10-30T23:59:59.999999+00:00 | 2026-11-06T03:54:46.165679+00:00 |
| [128. www.enel.com: alessandra stabilini](<https://www.enel.com/investors/governance/board-of-directors/alessandra-stabilini>) | Unverified; observation only | 2026-11-05T23:22:17.671204+00:00 |
| [129. www.enel.com: alessandro monteduro](<https://www.enel.com/investors/governance/board-of-directors/alessandro-monteduro>) | Unverified; observation only | 2026-11-05T23:22:17.949829+00:00 |
| [130. www.enel.com: dario frigerio](<https://www.enel.com/investors/governance/board-of-directors/dario-frigerio>) | Unverified; observation only | 2026-11-05T23:22:17.949693+00:00 |
| [131. www.enel.com: federica seganti](<https://www.enel.com/investors/governance/board-of-directors/federica-seganti>) | Unverified; observation only | 2026-11-05T23:22:17.599458+00:00 |
| [132. www.enel.com: flavio cattaneo](<https://www.enel.com/investors/governance/board-of-directors/flavio-cattaneo>) | Unverified; observation only | 2026-11-05T23:22:18.183628+00:00 |
| [133. www.enel.com: johanna arbib](<https://www.enel.com/investors/governance/board-of-directors/johanna-arbib>) | Unverified; observation only | 2026-11-05T23:22:18.264090+00:00 |
| [134. www.enel.com: mario corsi](<https://www.enel.com/investors/governance/board-of-directors/mario-corsi>) | Unverified; observation only | 2026-11-05T23:22:18.140412+00:00 |
| [135. www.enel.com: paolo scaroni](<https://www.enel.com/investors/governance/board-of-directors/paolo-scaroni>) | Unverified; observation only | 2026-11-05T23:22:17.921959+00:00 |
| [136. www.enel.com: tiziana de luca](<https://www.enel.com/investors/governance/board-of-directors/tiziana-de-luca>) | Unverified; observation only | 2026-11-05T23:22:18.002145+00:00 |
| [137. www.enel.com: recommendations](<https://www.enel.com/investors/investing/recommendations>) | Unverified; observation only | 2026-11-05T23:20:39.815911+00:00 |
| [138. www.enel.com: 3sun gigafactory](<https://www.enel.com/it/azienda/3sun-gigafactory>) | Unverified; observation only | 2026-11-06T03:56:57.569800+00:00 |
| [139. www.enelgreenpower.com: enel green power firma accordo finanziamento agevolato con unione europea gigafactory pannelli solari sicilia.pdf](<https://www.enelgreenpower.com/content/dam/enel-egp/documenti/comunicati-stampa/ita/enel-green-power-firma-accordo-finanziamento-agevolato-con-unione-europea-gigafactory-pannelli-solari-sicilia.pdf>) | Unverified; observation only | 2026-11-06T03:56:57.078000+00:00 |
| [140. www.flaeicisl.org: 3sun il valore della contrattazione](<https://www.flaeicisl.org/circolari/3sun-il-valore-della-contrattazione>) | Unverified; observation only | 2026-11-06T03:42:52.030495+00:00 |
| [141. www.ft.dk: 3125353.pdf](<https://www.ft.dk/samling/20251/almdel/eru/spm/8/svar/2196410/3125353.pdf>) | Unverified; observation only | 2026-11-06T04:02:05.931138+00:00 |
| [142. www.gazzettaufficiale.it: pdf](<https://www.gazzettaufficiale.it/eli/gu/2010/10/01/230/sg/pdf>) | Unverified; observation only | 2026-11-06T03:48:02.272318+00:00 |
| [143. www.gazzettaufficiale.it: pdf](<https://www.gazzettaufficiale.it/eli/gu/2014/08/27/198/sg/pdf>) | Unverified; observation only | 2026-11-06T03:47:57.826253+00:00 |
| [144. www.gov.br: mercado livre de energia entenda como funciona a migracao e as regras para contratacao de energia](<https://www.gov.br/mme/pt-br/assuntos/noticias/julho-26/mercado-livre-de-energia-entenda-como-funciona-a-migracao-e-as-regras-para-contratacao-de-energia>) | Unverified; observation only | 2026-11-06T03:42:48.743050+00:00 |
| [145. www.infineon.com: infpr202608 125e.pdf](<https://www.infineon.com/assets/row/public/documents/corporate/press/2026/infpr202608-125e.pdf>) | 2026-08-05T23:59:59.999999+00:00 | 2026-11-05T23:22:29.509633+00:00 |
| [146. www.infineon.com: 2025 annual report v01 00 en.pdf](<https://www.infineon.com/row/public/documents/corporate/investors/annual-reports/2025/2025-annual-report-v01-00-en.pdf>) | Unverified; observation only | 2026-11-05T23:16:54.169684+00:00 |
| [147. www.luminus.be: public disclosure](<https://www.luminus.be/nl/pro/elektrisch-rijden/laadpalen-en-kabels/>) | Unverified; observation only | 2026-11-06T03:46:34.741042+00:00 |
| [148. www.sec.gov: asml 20251231.htm](<https://www.sec.gov/Archives/edgar/data/0000937966/000162828026011378/asml-20251231.htm>) | 2026-02-25T23:59:59.999999+00:00 | 2026-11-05T23:15:17.957975+00:00 |
| [149. www.sec.gov: nxpi 20251231.htm](<https://www.sec.gov/Archives/edgar/data/1413447/000141344726000008/nxpi-20251231.htm>) | 2026-02-19T23:59:59.999999+00:00 | 2026-11-05T23:11:05.851384+00:00 |
| [150. www.sec.gov: nxpi 20260927.htm](<https://www.sec.gov/Archives/edgar/data/1413447/000141344726000059/nxpi-20260927.htm>) | 2026-10-27T23:59:59.999999+00:00 | 2026-11-05T23:11:06.201098+00:00 |
| [151. www.sec.gov: stm 20251231.htm](<https://www.sec.gov/Archives/edgar/data/932787/000093278726000009/stm-20251231.htm>) | 2026-02-26T23:59:59.999999+00:00 | 2026-11-05T23:11:07.067078+00:00 |
| [152. www.sec.gov: stm 6k q3x2026.htm](<https://www.sec.gov/Archives/edgar/data/932787/000093278726000094/stm-6k_q3x2026.htm>) | 2026-11-04T23:59:59.999999+00:00 | 2026-11-05T23:12:05.609245+00:00 |
| [153. www.sec.gov: pressreleasefinancialresul.htm](<https://www.sec.gov/Archives/edgar/data/937966/000162828026065813/pressreleasefinancialresul.htm>) | 2026-10-14T23:59:59.999999+00:00 | 2026-11-05T23:12:45.461183+00:00 |
| [154. www.senato.it: articolo 99](<https://www.senato.it/istituzione/la-costituzione/parte-ii/titolo-iii/sezione-iii/articolo-99>) | Unverified; observation only | 2026-11-06T03:48:04.482559+00:00 |
| [155. www.siemens-energy.com: supervisory board.html](<https://www.siemens-energy.com/global/en/home/company/supervisory-board.html>) | Unverified; observation only | 2026-11-05T23:17:23.380883+00:00 |
| [156. www.siemens-energy.com: pekka lundmark succeeds matthias rebellius on siemens energy sup.html](<https://www.siemens-energy.com/global/en/home/press-releases/pekka-lundmark-succeeds-matthias-rebellius-on-siemens-energy-sup.html>) | 2026-09-24T23:59:59.999999+00:00 | 2026-11-06T01:27:54.080974+00:00 |
| [157. www.siemensgamesa.com: meadow offshore wind manufacturing project.html](<https://www.siemensgamesa.com/global/en/home/products-and-services/offshore/meadow-offshore-wind-manufacturing-project.html>) | Unverified; observation only | 2026-11-06T03:56:57.269974+00:00 |
| [158. www.siemensgamesa.com: pivot project.html](<https://www.siemensgamesa.com/global/en/home/products-and-services/offshore/pivot-project.html>) | Unverified; observation only | 2026-11-06T03:42:51.007584+00:00 |
| [159. www.veolia.com: Finance Veolia URD 2025 en.pdf](<https://www.veolia.com/sites/g/files/dvc4206/files/document/2026/03/Finance_Veolia_URD_2025_en.pdf>) | 2026-03-26T23:59:59.999999+00:00 | 2026-11-05T23:12:25.008630+00:00 |
| [160. www.veolia.com: Finance Veolia operating financial review Q3 2026.pdf](<https://www.veolia.com/sites/g/files/dvc4206/files/document/2026/11/Finance_Veolia_operating_financial_review_Q3_2026.pdf>) | 2026-11-05T23:59:59.999999+00:00 | 2026-11-05T23:12:24.934076+00:00 |
| [161. www.vestas.com: Vestas Annual Report 2025.pdf](<https://www.vestas.com/content/dam/vestas-com/global/en/investor/reports-and-presentations/financial/2025/fy-2025/Vestas%20Annual%20Report%202025.pdf>) | 2026-02-05T23:59:59.999999+00:00 | 2026-11-05T23:15:12.873128+00:00 |

---

# Evaluation of eu-clean-air, edition 2026-Q4.r1-sample

Author `nxyziggy`, scores as of 2026-11-06T04:39:01+00:00. Bound to the snapshot payload with SHA-256 `21edeab72ef319fb41897110e101946b02595d0d350af393b5b73c58b0439327`.

Author-published and not independently reviewed. Check the signature and binding with `public-pilot verify-evaluation`.

## Method

EU clean-air three-pillar research with confirmed links and assigned campaign penalties, version eu\_confirmed\_links\_half\_campaign\_penalty\_v1.

This separate EU variant retains the three-pillar scoring and portfolio-construction methods: company execution (P1), industrial-policy support (P2), and industrial-network position (P3). The normalized pillars combine multiplicatively with the recorded inception-quarter weights of 30%, 55% and 15%, respectively. Component, pillar and composite outputs below are copied from the frozen completed scorecards, with no recomputation using later news or prices.

EU-specific choices are the midpoint of each disclosed lobbying band; fixed grant FX at the verified publication date of the exact amount; a network limited to confirmed links in a frozen 15-company source set; and a half-maximum campaign-factor penalty when the amount is undisclosed. The resulting point scores are model-assigned for Alfen, Siemens Energy and Nel. Enel is evidence-complete only within this selected scope. The defaults and remaining unknown raw values are disclosed separately.

The four completed eligible companies, not the 15 network references, define the selection population. Scores below the lower-quartile exit threshold receive zero weight. The median is the re-entry threshold and the upper quartile identifies the top group; no re-entry occurs in this initial allocation. Allocation starts with each surviving company's P3 divided by the sum of survivor P3 values in one 100% clean-air group. The first projection clips these normalized weights to 0.5–1.5 times equal weight (16.6667%–50% for three survivors). Any residual is divided equally among the companies that can move in its direction without remaining at a bound, then clipping and equal redistribution repeat until the total is restored within numerical tolerance. These first bounds do not bind in this sample. The separate 35% portfolio position cap is then applied within the group using the same equal-residual projection, with a zero lower bound. If the group cannot absorb its budget under that cap, the unused budget remains cash. There is no proportional P3 redistribution at this second step. Here P3 values 0.3132 (Alfen), 0.3513 (Siemens Energy) and 0.2750 (Nel) sum to 0.9395. Initial weights are 33.33688132%, 37.39222991% and 29.27088877%. Capping Siemens Energy at 35% releases 2.39222991 percentage points; Alfen and Nel each receive 1.19611495 points. Final weights are 34.53299627%, 35% and 30.46700373%, with the original exact serialized decimals retained below. A higher composite rank therefore need not imply a larger weight. Enel is the recorded startup exit and has no positive target; no actual sale is represented.

Evidence was frozen on November 6, 2026 at 04:24:51.531890 UTC. The model treatment and allocation were recorded at 04:39:01 UTC that day. Publication of this free demo does not update those records. It is for reading and fictional offline previews only; the symbols identify original research listings and do not certify availability at any broker.

| Threshold | Value |
| --- | ---: |
| exit | 0.48925 |
| overweight | 0.5984499999999999 |
| reentry | 0.54035 |

## Companies

| Rank | Symbol | p1 | p1a | p1b | p1c | p1d | p1e | p1f | p2 | p3 | p3a | p3b | Composite | Decision | Weight |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | ENR.DE | 0.6429 | 0.5 | 1.0 | 0.5 | 0.5 | 0.5051 | 0.7174 | 0.8447 | 0.3513 | 0.2521 | 0.5 | 0.6928 | `include` | 0.35 |
| 2 | NEL.OL | 0.3892 | 0.5 | 0.0 | 0.5 | 0.5 | 0.5215 | 0.6504 | 0.8184 | 0.275 | 0.125 | 0.5 | 0.567 | `include` | 0.30467003725385844 |
| 3 | ALFEN.AS | 0.4393 | 0.5 | 0.0801 | 0.5 | 0.5 | 0.6351 | 0.8846 | 0.6171 | 0.3132 | 0.1886 | 0.5 | 0.5137 | `include` | 0.34532996274614153 |
| 4 | ENEL.MI | 0.4689 | 0.5 | 0.2242 | 0.5 | 0.5264 | 0.6876 | 0.6991 | 0.4025 | 0.3132 | 0.1886 | 0.5 | 0.4159 | `exit` | 0.0 |

## Notes

- **ENR.DE**: Siemens Energy. MODEL\_ASSIGNED: campaign raw amount is null; half-maximum campaign penalty applied. Highest composite; the 35% position cap binds. Confirmed network customers are EDF/Enedis and Orsted. The ROIC input is a strategy-derived 94.6796% for the TTM to June 30, 2026, using latest capital after subtracting cash; see the calculation in REPORT.md.
- **NEL.OL**: Nel. MODEL\_ASSIGNED: campaign raw amount and raw ROIC are null. Half-maximum campaign penalty applied; all values in the verified ROIC interval give the same zero ROIC-spread component. No qualifying network link confirmed in the frozen set; this does not mean no customers or suppliers exist.
- **ALFEN.AS**: Alfen. MODEL\_ASSIGNED: campaign raw amount is null; half-maximum campaign penalty applied. Lobbying band includes an issuer-described event cost estimate. Confirmed customer link to EDF/Luminus. P3-based allocation explains its greater weight than Nel despite a lower composite.
- **ENEL.MI**: Enel. Evidence-complete within the selected EU scope, including neutral model treatments and analyst judgments; not independently reviewed. Disclosed campaign amount is zero within its stated perimeter. Score is below the four-company exit threshold, so the archived startup decision is exit with zero weight. No holding or executed sale is implied.

## Defaults disclosed

- Subsidy-utilization P1a and innovation-spillover P3b are fixed at 0.5 for all four companies. These are model treatments, not observed grant utilization or innovation measurements.
- The insider-ownership contribution within governance is neutral at 0.5 for all four companies. An 8% cost-of-capital fallback is used. Missing raw ownership and cost-of-capital observations are not fabricated.
- Capital-expenditure execution P1c is 0.5 for all four because no approved comparable plan/actual pair is available. Analyst-target P1d is 0.5 for Alfen, Siemens Energy and Nel because an approved complete consensus set is unavailable; Enel retains its assessed target data.
- EU lobbying uses the midpoint of each closed EU Transparency Register cost band, converted at the relevant fiscal-period-end ECB rate. The endpoints are retained in the report. These are filed cost estimates, not exact lobbying cash expenses; national-register and intermediary amounts are not added on top.
- Alfen, Siemens Energy and Nel have no verified campaign amount for the specified period. Their raw amounts remain null. Each receives a model-assigned penalty of 0.10 in P1f, half of the campaign factor maximum penalty of 0.20. This is not a statement that the issuer spent a particular amount. Enel retains its disclosed zero within the stated reporting perimeter.
- Nel raw return on invested capital remains null. Its verified interval of -0.5882922370408002 to -0.4169893062532083 produces the same zero ROIC-spread component throughout at the configured cost of capital. An exact raw ROIC is not invented.
- Siemens Energy's ROIC input of 0.9467959966831865 is strategy-derived for July 1, 2025–June 30, 2026, not an issuer-reported ratio. It is TTM operating income times (1 minus the TTM tax-expense/pretax-income rate, clamped to 0–50%), divided by latest total equity plus current and non-current debt minus cash. The denominator is not averaged; subtracting EUR 11,088 million cash leaves EUR 3,042 million invested capital. Reported operating income is not adjusted for special items. REPORT.md shows the statement lines and arithmetic. The derived 94.6796% ratio and capped P1b score of 1.0 are retained; differently defined ROIC or ROCE measures are not interchangeable with this input.
- Network counts use only confirmed links in a frozen source set of 15 reference companies. Zero means no qualifying link was confirmed in that set. The degree proxy is not a complete supply-chain census or a Leontief input-output measure. The disputed reverse Enel-to-EDF link is excluded and shown as a sensitivity.
- Eligible grant face amounts are converted using the ECB rate on the earliest verified publication date of the exact amount, then frozen until that amount changes. Award face amounts do not establish cash received or unconditional future entitlement.
- Governance, delivery, capital-allocation, substitutability and policy-risk values include dated analyst judgments. The variant is author-published and has not been independently reviewed.
- Only the four completed eligible scorecards define this edition and its selection thresholds. The wider 15-company set is used for network research; this publication does not assign scores or portfolio decisions to the other 11 companies.
- The inception-quarter calculation uses one clean-air allocation group and a 35% position cap. These are archived research targets, not account holdings, orders, or a live portfolio. Exact serialized target decimals are preserved without re-optimization.
