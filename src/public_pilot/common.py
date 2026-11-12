"""Strict, data-only parsing and deterministic identities."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_DOCUMENT_BYTES = 2_000_000


class Refused(ValueError):
    """The requested operation cannot satisfy the runtime contract."""


def require(condition, message):
    if not condition:
        raise Refused(message)


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def loads(raw: str | bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_):
        raise Refused("Non-finite JSON number")

    require(len(raw) <= MAX_DOCUMENT_BYTES, "Document too large")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Refused("Invalid JSON document") from exc


def read_json(path):
    with Path(path).open("rb") as stream:
        return loads(stream.read(MAX_DOCUMENT_BYTES + 1))


def decimal(value) -> Decimal:
    require(isinstance(value, (str, int)) and not isinstance(value, bool),
            "Decimal values must be strings or integers")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise Refused("Invalid decimal value") from exc
    require(result.is_finite() and abs(result) <= Decimal("1e15"),
            "Non-finite or excessive decimal value")
    return result


def timestamp(value: str) -> datetime:
    require(isinstance(value, str) and len(value) <= 40, "Invalid timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused("Invalid timestamp") from exc
    require(result.tzinfo is not None, "Timestamp must include timezone")
    return result.astimezone(timezone.utc)


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(instant: datetime) -> str:
    return instant.astimezone(timezone.utc).isoformat()


def fields(obj, required, optional=()):
    require(isinstance(obj, dict), "Expected an object")
    require(set(required) <= obj.keys() <= set(required) | set(optional),
            "Missing or unknown document fields")
