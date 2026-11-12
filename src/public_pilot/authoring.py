"""Author tools: keys, signing and self-checks. Private keys never enter a Git checkout."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import stat

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

from .bundles import RELEASE_FORMAT, RELEASE_NAME, check_release, inventory, read_member_json
from .common import MAX_DOCUMENT_BYTES, Refused, canonical, digest, require, timestamp
from .evaluation import FORMAT as EVALUATION_FORMAT, verify_evaluation
from .packages import FORMAT, IDENTIFIER, resolve_chain

KEY_BYTES = 32


def fingerprint(public_key):
    """SHA-256 of the raw 32-byte Ed25519 public key, lowercase hex."""
    try:
        raw = base64.b64decode(public_key, validate=True)
    except (ValueError, TypeError) as exc:
        raise Refused("A public key is the standard base64 of 32 bytes") from exc
    require(len(raw) == KEY_BYTES, "A public key is the standard base64 of 32 bytes")
    return hashlib.sha256(raw).hexdigest()


def public_key(private):
    return base64.b64encode(private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()


def in_git_checkout(path):
    """True if the path or any directory above it holds a .git entry."""
    try:
        resolved = Path(path).resolve()
    except (OSError, RuntimeError) as exc:  # Python 3.11 raises RuntimeError on a symbolic link loop
        raise Refused("Key path cannot be resolved; it may contain a symbolic link loop") from exc
    for parent in resolved.parents:
        marker = parent / ".git"
        if marker.exists() or marker.is_symlink():
            return True
    return False


def keygen(out):
    """Write a new raw Ed25519 private key with mode 0600. Never overwrites."""
    path = Path(out)
    require(not in_git_checkout(path), "Keep signing keys outside every Git checkout")
    private = Ed25519PrivateKey.generate()
    raw = private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    try:
        handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except FileExistsError as exc:
        raise Refused("Key file already exists; keygen never overwrites") from exc
    try:
        os.fchmod(handle, 0o600)
        view = memoryview(raw)
        while view:
            view = view[os.write(handle, view):]
        os.fsync(handle)
    finally:
        os.close(handle)
    key = public_key(private)
    return {"status": "created", "key": str(path), "public_key": key, "fingerprint_sha256": fingerprint(key)}


def load_private_key(path):
    """Read a signing key only if it is a private, unlinked regular file outside every Git checkout."""
    path = Path(path)
    require(not in_git_checkout(path), "Signing keys must live outside every Git checkout")
    info = os.lstat(path)
    require(stat.S_ISREG(info.st_mode), "The signing key must be a regular file, not a link")
    require(info.st_nlink == 1, "The signing key must not be hard-linked")
    require(info.st_mode & 0o077 == 0, "The signing key must have owner-only permissions (chmod 600)")
    handle = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(handle, "rb") as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (info.st_dev, info.st_ino), "The signing key changed while opening")
        raw = stream.read(KEY_BYTES + 1)
    require(len(raw) == KEY_BYTES, "The signing key must be a raw 32-byte Ed25519 private key")
    return Ed25519PrivateKey.from_private_bytes(raw)


def sign(private, body):
    return {**body, "signature": base64.b64encode(private.sign(canonical(body))).decode()}


def envelope(private, key_id, payload, kind="snapshot"):
    return sign(private, {"format": FORMAT, "kind": kind, "key_id": key_id, "payload": payload})


def self_trust(private, key_id, payload):
    """A one-key trust store for the signer's own self-check."""
    return {key_id: {"public_key": public_key(private), "author_id": payload.get("author_id"),
                     "packages": [payload.get("package_id")], "allow_paper": True}}


def check_key_id(key_id):
    require(isinstance(key_id, str) and IDENTIFIER.fullmatch(key_id),
            "Key IDs use 1-96 letters, digits, '.', '_' or '-', starting with a letter or digit")


def signing_instant(payload, now, as_of):
    """The self-check instant: now, or an explicit past instant for demonstration editions."""
    if as_of is None:
        return now
    require(payload.get("purpose") == "demo", "--as-of may only sign editions with purpose demo")
    instant = timestamp(as_of)
    require(instant <= now, "--as-of cannot be in the future")
    return instant


def sign_snapshot(private, key_id, payload, now, as_of=None):
    check_key_id(key_id)
    require(isinstance(payload, dict), "Expected an unsigned payload object")
    instant = signing_instant(payload, now, as_of)
    document = envelope(private, key_id, payload)
    resolve_chain([document], self_trust(private, key_id, payload), instant)
    return document


def sign_delta(private, key_id, base, payload, now, as_of=None):
    """A delta that turns the base payload into the new one; it must match the full snapshot exactly."""
    check_key_id(key_id)
    require(isinstance(base, dict) and isinstance(payload, dict), "Expected unsigned payload objects")
    instant = signing_instant(payload, now, as_of)
    replacements = {k: v for k, v in payload.items() if base.get(k) != v}
    body = {"package_id": payload.get("package_id"), "base_sha256": digest(base),
            "result_sha256": digest(payload), "replace": replacements}
    document = envelope(private, key_id, body, "delta")
    resolved = resolve_chain([envelope(private, key_id, base), document],
                             self_trust(private, key_id, payload), instant)
    require(resolved == payload, "The delta does not reproduce the new payload")
    return document


def sign_evaluation(private, key_id, payload, snapshot, now):
    """Sign an evaluation and verify it against the edition's snapshot, which must carry the same key."""
    check_key_id(key_id)
    require(isinstance(payload, dict), "Expected an unsigned evaluation payload object")
    document = sign(private, {"format": EVALUATION_FORMAT, "key_id": key_id, "payload": payload})
    verify_evaluation(document, snapshot, self_trust(private, key_id, payload), now)
    return document


def sign_release(private, key_id, root, snapshot, now):
    """Sign every regular file under root except release.json, then verify the result in place."""
    check_key_id(key_id)
    root = Path(root)
    require(not os.path.lexists(root / RELEASE_NAME), "release.json already exists; remove it to re-sign")
    files = inventory(root)
    require(snapshot in files, "Snapshot is outside the release inventory")
    edition = read_member_json(root / snapshot)
    require(isinstance(edition, dict) and isinstance(edition.get("payload"), dict),
            "The release snapshot must be a signed envelope")
    payload = edition["payload"]
    release = sign(private, {"format": RELEASE_FORMAT, "key_id": key_id, "package_id": payload.get("package_id"),
                             "snapshot": snapshot, "files": files})
    check_release(root, release, self_trust(private, key_id, payload), now)
    return release


def write_new(path, document):
    """Write a signed document as UTF-8 JSON. Existing files are never overwritten."""
    data = (json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    require(len(data) <= MAX_DOCUMENT_BYTES, "Document too large")
    try:
        handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise Refused(f"{path} already exists; signed documents are never overwritten") from exc
    with os.fdopen(handle, "wb") as stream:
        stream.write(data)
    return str(path)
