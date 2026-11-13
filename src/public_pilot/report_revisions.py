"""Exact, maintainer-reviewed report revisions; never load permissions from a proposed tree.

Merge this code before the data PR. The normal catalog signature checks still apply.
An entry permits only its named before/after bytes, including the signed release.
It grants no general right to rewrite a report, alter research or roll back a revision.
"""
from .bundles import file_sha256


_MATERIALS_RESEARCH = {
    "edition.snapshot.json": "672cc6f75cb568628ebf959d6aabf0a6d9f6c8548dc7d682b75df7cec3221b29",
    "evaluation.json": "ab2ae93d8e07c1ad80fe4c7934fe50cfa34832788b4f54cffe39b2f162baaebe",
    "account.fixture.json": "99399e18352a0d8b0324e68ee57ed3bf3bfbc0680706b83f5f3edd791bcecef4",
}

# Editorial introduction only, dated 2026-11-13. Scores, weights, evidence,
# edition identity and the complete rendered evaluation remain unchanged.
REPORT_REVISIONS = {
    "history/usmaterials/2026-Q4": (
        {**_MATERIALS_RESEARCH,
         "REPORT.md": "0f73d4811dcc21d48a54ea1bb66f3c403ae6554cd981329068407c8f65505b28",
         "release.json": "4af4499cb5e96adfb007b4e825a0189ac4df3068c9f235143863b6c741e37a66"},
        {**_MATERIALS_RESEARCH,
         "REPORT.md": "7dbe05c792debbfa7d3f056677af353933f2d092cb69280b252512a1cf8003c3",
         "release.json": "f98a5860242cb6888ff0c726b4c0e551ee0a3cd9b6c36c80cdaedb5b10a6c66a"},
    ),
}


def matches_report_revision(where, before, after):
    """Only trusted code can approve a transition; all five files must match on both sides."""
    revision = REPORT_REVISIONS.get(where)
    if revision is None:
        return False
    return all(file_sha256(directory / name) == expected
               for directory, hashes in zip((before, after), revision)
               for name, expected in hashes.items())
