"""Signed evaluation documents: an author's scores, selection and weights, bound to one edition by hash."""
from __future__ import annotations

from decimal import Decimal
import re
import unicodedata

from .bundles import trusted_grant, verify_signature
from .common import Refused, decimal, digest, fields, require, timestamp
from .packages import IDENTIFIER, SYMBOL, resolve_historical

FORMAT = "public-pilot-evaluation-v1"
DOCUMENT_FIELDS = ("format", "key_id", "payload", "signature")
PAYLOAD_FIELDS = ("package_id", "edition_id", "author_id", "package_sha256", "as_of", "method",
                  "thresholds", "companies", "defaults_disclosed")
COMPANY_FIELDS = ("rank", "composite", "components", "decision", "weight", "note")
DECISIONS = ("include", "exclude", "exit", "reentry", "zero_weight")
# Plain decimal notation: optional minus, up to 15 integer digits, up to 18 fractional digits.
DECIMAL = re.compile(r"^-?(0|[1-9][0-9]{0,14})(\.[0-9]{1,18})?$")
WEIGHT = re.compile(r"^(0(\.[0-9]{1,18})?|1(\.0{1,18})?)$")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_COMPONENTS = 40
MAX_THRESHOLDS = 40
MAX_COMPANIES = 100
LIMITS = {"method name": 200, "method version": 50, "method description": 20_000, "note": 2_000,
          "default disclosure": 1_000}


def text(value, what, *, minimum=0):
    require(isinstance(value, str) and minimum <= len(value) <= LIMITS[what],
            f"Invalid evaluation {what}: text of at most {LIMITS[what]} characters")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise Refused(f"Invalid evaluation {what}: not valid Unicode text") from exc


def number(value, what, pattern=DECIMAL):
    require(isinstance(value, str) and pattern.fullmatch(value),
            f"Evaluation {what} values must be plain decimal strings")
    return Decimal(value)


def validate_payload(payload):
    """Structure of an evaluation payload. Its binding to a snapshot is checked by check_binding."""
    fields(payload, PAYLOAD_FIELDS)
    for name in ("package_id", "edition_id", "author_id"):
        require(isinstance(payload[name], str) and IDENTIFIER.fullmatch(payload[name]),
                "Invalid evaluation identifier")
    require(isinstance(payload["package_sha256"], str) and SHA256.fullmatch(payload["package_sha256"]),
            "package_sha256 must be a lowercase SHA-256 hex digest")
    timestamp(payload["as_of"])
    method = payload["method"]
    fields(method, ("name", "version", "description"))
    text(method["name"], "method name", minimum=1)
    text(method["version"], "method version", minimum=1)
    text(method["description"], "method description")
    thresholds = payload["thresholds"]
    require(isinstance(thresholds, dict) and len(thresholds) <= MAX_THRESHOLDS,
            f"Thresholds are a map of at most {MAX_THRESHOLDS} entries")
    for name, value in thresholds.items():
        require(NAME.fullmatch(name), "Invalid threshold name")
        number(value, "threshold")
    companies = payload["companies"]
    require(isinstance(companies, dict) and 1 <= len(companies) <= MAX_COMPANIES,
            f"Companies are a map of 1 to {MAX_COMPANIES} symbols")
    for symbol, company in companies.items():
        require(SYMBOL.fullmatch(symbol), "Invalid evaluation symbol")
        fields(company, COMPANY_FIELDS)
        require(type(company["rank"]) is int and 1 <= company["rank"] <= MAX_COMPANIES,
                "Evaluation ranks are integers starting at 1")
        number(company["composite"], "composite")
        components = company["components"]
        require(isinstance(components, dict) and len(components) <= MAX_COMPONENTS,
                f"At most {MAX_COMPONENTS} components per company")
        for name, value in components.items():
            require(NAME.fullmatch(name), "Invalid component name")
            number(value, "component")
        require(company["decision"] in DECISIONS, "Unknown evaluation decision")
        number(company["weight"], "weight", WEIGHT)
        text(company["note"], "note")
    disclosed = payload["defaults_disclosed"]
    require(isinstance(disclosed, list) and len(disclosed) <= 200, "defaults_disclosed is a list of at most 200 entries")
    for item in disclosed:
        text(item, "default disclosure", minimum=1)
    return payload


def check_binding(payload, snapshot):
    """The evaluation belongs to exactly this snapshot payload."""
    require(payload["package_sha256"] == digest(snapshot),
            "Evaluation is bound to a different snapshot: package_sha256 mismatch")
    for name in ("package_id", "edition_id", "author_id"):
        require(payload[name] == snapshot[name], f"Evaluation {name} does not match the snapshot")
    companies = payload["companies"]
    require(set(companies) == set(snapshot["universe"]), "Evaluation companies must equal the snapshot universe")
    for symbol in sorted(companies):
        require(Decimal(companies[symbol]["weight"]) == decimal(snapshot["targets"].get(symbol, "0")),
                f"Evaluation weight for {symbol} differs from the payload target")
    ranked = sorted(companies.values(), key=lambda company: company["rank"])
    require([company["rank"] for company in ranked] == list(range(1, len(ranked) + 1)),
            "Evaluation ranks must be a permutation of 1 to n")
    composites = [Decimal(company["composite"]) for company in ranked]
    require(all(higher >= lower for higher, lower in zip(composites, composites[1:])),
            "Evaluation ranks must follow descending composite order")


def check_document(document):
    require(isinstance(document, dict), "Expected a signed evaluation document")
    fields(document, DOCUMENT_FIELDS)
    require(document["format"] == FORMAT, "Unsupported evaluation format")
    return validate_payload(document["payload"])


def verify_document(document, trust):
    """Signature by a key trusted for the evaluation's package and author."""
    payload = check_document(document)
    grant = trusted_grant(trust, document["key_id"])
    verify_signature(document, grant)
    require(payload["package_id"] in grant["packages"], "Publisher key is not trusted for this package")
    require(payload["author_id"] == grant["author_id"], "Publisher author mismatch")
    return payload


def verify_evaluation(document, snapshot_envelope, trust, now):
    """Read-only: the snapshot resolves in historical mode, then the evaluation must match it."""
    require(isinstance(snapshot_envelope, dict), "Expected a signed snapshot")
    snapshot, expired = resolve_historical([snapshot_envelope], trust, now)
    payload = verify_document(document, trust)
    check_binding(payload, snapshot)
    return {"status": "verified", "package_id": payload["package_id"], "edition_id": payload["edition_id"],
            "package_sha256": payload["package_sha256"], "companies": len(payload["companies"]),
            "expired": expired}


INLINE = re.compile(r"([\\`*_\[\]<>|~])")
LINE_START = re.compile(r"^([#=+-]|\d+[.)])")


def escape(value):
    """Author text as inert Markdown: one line; no markup, links, HTML, control or format characters."""
    visible = "".join(c for c in value if unicodedata.category(c) not in ("Cc", "Cf") or c.isspace())
    return INLINE.sub(r"\\\1", " ".join(visible.split()))


def paragraph(value):
    line = escape(value)
    return "\\" + line if LINE_START.match(line) else line


def render(document):
    """A Markdown report of an evaluation. Structure is validated; verify signatures with verify-evaluation."""
    payload = check_document(document)
    method = payload["method"]
    companies = sorted(payload["companies"].items(), key=lambda item: item[1]["rank"])
    names = sorted({name for _, company in companies for name in company["components"]})
    lines = [f"# Evaluation of {payload['package_id']}, edition {payload['edition_id']}", "",
             f"Author `{payload['author_id']}`, scores as of {escape(payload['as_of'])}. Bound to the snapshot "
             f"payload with SHA-256 `{payload['package_sha256']}`.", "",
             "Author-published and not independently reviewed. Check the signature and binding with "
             "`public-pilot verify-evaluation`.", "",
             "## Method", "", f"{escape(method['name'])}, version {escape(method['version'])}."]
    lines += [line for part in method["description"].split("\n\n") if part.strip()
              for line in ("", paragraph(part))]
    if payload["thresholds"]:
        lines += ["", "| Threshold | Value |", "| --- | ---: |"]
        lines += [f"| {escape(name)} | {value} |" for name, value in sorted(payload["thresholds"].items())]
    header = ["Rank", "Symbol", *(escape(name) for name in names), "Composite", "Decision", "Weight"]
    lines += ["", "## Companies", "", "| " + " | ".join(header) + " |",
              "| " + " | ".join(["---:", "---", *("---:" for _ in names), "---:", "---", "---:"]) + " |"]
    for symbol, company in companies:
        cells = [str(company["rank"]), symbol, *(company["components"].get(name, "") for name in names),
                 company["composite"], f"`{company['decision']}`", company["weight"]]
        lines.append("| " + " | ".join(cells) + " |")
    notes = [(symbol, company["note"]) for symbol, company in companies if company["note"].strip()]
    if notes:
        lines += ["", "## Notes", ""] + [f"- **{symbol}**: {escape(note)}" for symbol, note in notes]
    lines += ["", "## Defaults disclosed", ""]
    lines += [f"- {escape(item)}" for item in payload["defaults_disclosed"]] or ["None."]
    return "\n".join(lines) + "\n"
