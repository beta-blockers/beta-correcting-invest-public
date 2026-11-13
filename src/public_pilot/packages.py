"""Verify completed snapshots and deltas. No discovery, inference, or code loading."""
from __future__ import annotations

import base64
import re
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .common import Refused, canonical, decimal, digest, fields, require, timestamp

FORMAT = "public-pilot-envelope-v1"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
SYMBOL = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
PAYLOAD_FIELDS = {
    "package_id", "edition_id", "author_id", "engine_major", "purpose",
    "published_at", "information_cutoff", "valid_until", "geographies",
    "policy_ids", "universe", "targets", "research", "evidence",
}


def validate_payload(payload, instant):
    fields(payload, PAYLOAD_FIELDS)
    for name in ("package_id", "edition_id", "author_id"):
        require(isinstance(payload[name], str) and IDENTIFIER.fullmatch(payload[name]),
                "Invalid package identifier")
    require(type(payload["engine_major"]) is int and payload["engine_major"] == 1,
            "Unsupported engine compatibility")
    require(payload["purpose"] in ("demo", "paper"), "Unsupported package purpose")
    cutoff = timestamp(payload["information_cutoff"])
    published = timestamp(payload["published_at"])
    expires = timestamp(payload["valid_until"])
    require(cutoff <= published <= instant < expires, "Expired or future-dated research")
    for name in ("geographies", "policy_ids", "universe"):
        values = payload[name]
        require(isinstance(values, list) and 0 < len(values) <= 100,
                "Invalid scope list")
        require(all(isinstance(v, str) and 0 < len(v) <= 100 for v in values),
                "Invalid scope value")
        require(len(values) == len(set(values)), "Duplicate scope value")
    require(all(SYMBOL.fullmatch(s) for s in payload["universe"]), "Invalid symbol")
    targets = payload["targets"]
    require(isinstance(targets, dict) and targets and set(targets) <= set(payload["universe"]),
            "Targets must belong to the declared universe")
    weights = [decimal(w) for w in targets.values()]
    require(all(0 <= w <= 1 for w in weights) and sum(weights) <= 1,
            "Invalid target weights; residual weight is cash")
    require(isinstance(payload["research"], str) and len(payload["research"]) <= 500_000,
            "Invalid research text")
    require(isinstance(payload["evidence"], list) and len(payload["evidence"]) <= 1000,
            "Invalid evidence list")
    for source in payload["evidence"]:
        fields(source, ("title", "url", "published_at"))
        require(isinstance(source["title"], str) and 0 < len(source["title"]) <= 500,
                "Invalid evidence title")
        require(isinstance(source["url"], str) and len(source["url"]) <= 2048,
                "Invalid evidence URL")
        url = urlsplit(source["url"])
        require(url.scheme == "https" and url.hostname and not url.username and not url.password,
                "Evidence URLs must be HTTPS references")
        require(timestamp(source["published_at"]) <= cutoff, "Evidence after cutoff")
    return payload


def verify_envelope(envelope, trust):
    fields(envelope, ("format", "kind", "key_id", "payload", "signature"))
    require(envelope["format"] == FORMAT and envelope["kind"] in ("snapshot", "delta"),
            "Unsupported package envelope")
    require(isinstance(envelope["key_id"], str), "Invalid publisher key ID")
    require(isinstance(trust, dict) and envelope["key_id"] in trust,
            "Publisher is not in the local trust store")
    grant = trust[envelope["key_id"]]
    fields(grant, ("public_key", "author_id", "packages", "allow_paper"))
    require(type(grant["allow_paper"]) is bool and isinstance(grant["packages"], list),
            "Invalid trust grant")
    body = {k: v for k, v in envelope.items() if k != "signature"}
    try:
        key = base64.b64decode(grant["public_key"], validate=True)
        signature = base64.b64decode(envelope["signature"], validate=True)
        Ed25519PublicKey.from_public_bytes(key).verify(signature, canonical(body))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise Refused("Publisher signature verification failed") from exc
    payload = envelope["payload"]
    require(isinstance(payload, dict) and payload.get("package_id") in grant["packages"],
            "Publisher key is not trusted for this package")
    return grant


def resolve_chain(proofs, trust, instant, *, check_freshness=True, trading=False):
    """Resolve a signed chain. trading is set for live previews and paper orders: every key must then allow
    paper, whatever the edition's purpose. A paper edition needs that permission for every use."""
    require(isinstance(proofs, list) and 1 <= len(proofs) <= 32, "Invalid package chain")
    payload = None
    for envelope in proofs:
        grant = verify_envelope(envelope, trust)
        body = envelope["payload"]
        previous = payload
        if envelope["kind"] == "snapshot":
            require(payload is None, "Only the first chain member can be a snapshot")
            payload = dict(body)
        else:
            fields(body, ("package_id", "base_sha256", "result_sha256", "replace"))
            require(payload is not None and body["base_sha256"] == digest(payload),
                    "Delta does not match the installed base")
            replacements = body["replace"]
            require(isinstance(replacements, dict) and replacements and
                    replacements.keys() <= PAYLOAD_FIELDS - {"package_id", "author_id", "purpose"},
                    "Invalid delta replacements")
            require(body["package_id"] == payload["package_id"], "Delta package mismatch")
            payload = {**payload, **replacements}
            require(digest(payload) == body["result_sha256"], "Delta result hash mismatch")
            require(payload["edition_id"] != previous["edition_id"] and
                    timestamp(payload["published_at"]) > timestamp(previous["published_at"]) and
                    timestamp(payload["information_cutoff"]) >= timestamp(previous["information_cutoff"]),
                    "Delta must advance the edition without moving its cutoff backwards")
        require(payload.get("author_id") == grant["author_id"], "Publisher author mismatch")
        require(grant["allow_paper"] or (payload.get("purpose") != "paper" and not trading),
                "This key is trusted only for demonstrations")
        # Historical bases may expire before an update; validate them at publication.
        at = instant if check_freshness and envelope is proofs[-1] else timestamp(payload["published_at"])
        validate_payload(payload, at)
    return payload


def resolve_historical(proofs, trust, now):
    """Read-only historical mode: an expired edition resolves, a future-dated one never does."""
    payload = resolve_chain(proofs, trust, now, check_freshness=False)
    require(timestamp(payload["published_at"]) <= now, "Future-dated research")
    return payload, now >= timestamp(payload["valid_until"])
