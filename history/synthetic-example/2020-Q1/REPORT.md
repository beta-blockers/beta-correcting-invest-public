# Evaluation of synthetic-example, edition synthetic-example-2020-q1

Author `synthetic-author`, scores as of 2019-12-31T00:00:00+00:00. Bound to the snapshot payload with SHA-256 `0aa977a30bef492bccb4ed4c31379dd9a955069d6e6fc023403a4fd711c69fbe`.

Author-published and not independently reviewed. Check the signature and binding with `public-pilot verify-evaluation`.

## Method

Fictional three-pillar score, version 1.0.

Invented for the demonstration. Each pillar is scored from 0 to 100 and the composite is their average. Companies at or above include\_min are selected; a company below exit\_below is sold.

| Threshold | Value |
| --- | ---: |
| exit\_below | 40 |
| include\_min | 55 |

## Companies

| Rank | Symbol | pillar\_1 | pillar\_2 | pillar\_3 | Composite | Decision | Weight |
| ---: | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | DEMOA | 80.0 | 70.2 | 67.0 | 72.4 | `include` | 0.45 |
| 2 | DEMOB | 62.1 | 60.3 | 61.5 | 61.3 | `include` | 0.35 |
| 3 | DEMOC | 31.2 | 32.5 | 50 | 37.9 | `exit` | 0 |

## Notes

- **DEMOA**: Fictional: highest composite.
- **DEMOC**: Fictional: below exit\_below; kept in the universe so that a holder can sell it.

## Defaults disclosed

- pillar\_3 for DEMOC is the neutral value 50 because no fictional filing was available.
