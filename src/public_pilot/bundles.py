"""Signed release inventories for data-only bundles. Nothing here executes bundle content."""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
import re
import stat

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .common import Refused, canonical, fields, loads, require, MAX_DOCUMENT_BYTES
from .packages import IDENTIFIER, resolve_historical

RELEASE_FORMAT = "public-pilot-release-v1"
RELEASE_NAME = "release.json"
RELEASE_FIELDS = ("format", "key_id", "package_id", "snapshot", "files", "signature")
MAX_FILES = 500
SHA256 = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_NAME = re.compile(r"[\x00-\x1f\x7f\\]")


def member_name_ok(name):
    """A relative POSIX path with no empty, '.', '..', control or backslash component."""
    if not isinstance(name, str) or not 0 < len(name) <= 512 or UNSAFE_NAME.search(name):
        return False
    try:
        name.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return all(part not in ("", ".", "..") for part in name.split("/"))


def open_member(path):
    """Open a regular, singly linked file without following a link or blocking on a FIFO."""
    try:
        handle = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    except FileNotFoundError as exc:
        raise Refused(f"File not found: {Path(path).name}") from exc
    except OSError as exc:
        raise Refused(f"Linked or unreadable file refused: {Path(path).name}") from exc
    info = os.fstat(handle)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(handle)
        raise Refused(f"Linked or special file refused: {Path(path).name}")
    return os.fdopen(handle, "rb")


def file_sha256(path):
    result = hashlib.sha256()
    with open_member(path) as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            result.update(chunk)
    return result.hexdigest()


def read_member_json(path):
    with open_member(path) as stream:
        return loads(stream.read(MAX_DOCUMENT_BYTES + 1))


def scan(root):
    """Every regular file under root as {relative POSIX name: path}; links and special files are refused."""
    root = Path(root)
    require(root.is_dir(), "Bundle directory not found")
    found = {}
    pending = [(root, "")]
    while pending:
        directory, prefix = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                name = prefix + entry.name
                require(member_name_ok(name), "Unsupported file name in bundle")
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    raise Refused(f"Linked bundle member refused: {name}")
                if stat.S_ISDIR(info.st_mode):
                    pending.append((Path(entry.path), name + "/"))
                    continue
                require(stat.S_ISREG(info.st_mode), f"Special file in bundle refused: {name}")
                require(info.st_nlink == 1, f"Hard-linked bundle member refused: {name}")
                found[name] = Path(entry.path)
                require(len(found) <= MAX_FILES + 1, "A release lists at most 500 files")
    return found


def inventory(root):
    """Hashes of every regular file under root except the root release.json."""
    files = scan(root)
    files.pop(RELEASE_NAME, None)
    require(1 <= len(files) <= MAX_FILES, "A release lists between 1 and 500 files")
    return {name: file_sha256(files[name]) for name in sorted(files)}


def trusted_grant(trust, key_id):
    require(isinstance(trust, dict) and isinstance(key_id, str) and key_id in trust,
            "Publisher is not in the local trust store")
    grant = trust[key_id]
    fields(grant, ("public_key", "author_id", "packages", "allow_paper"))
    require(type(grant["allow_paper"]) is bool and isinstance(grant["packages"], list), "Invalid trust grant")
    return grant


def verify_signature(document, grant):
    """Ed25519 over the canonical document without its signature, as for package envelopes."""
    body = {k: v for k, v in document.items() if k != "signature"}
    try:
        key = base64.b64decode(grant["public_key"], validate=True)
        signature = base64.b64decode(document["signature"], validate=True)
        Ed25519PublicKey.from_public_bytes(key).verify(signature, canonical(body))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise Refused("Publisher signature verification failed") from exc


def validate_release(release):
    fields(release, RELEASE_FIELDS)
    require(release["format"] == RELEASE_FORMAT, "Unsupported release format")
    require(isinstance(release["key_id"], str), "Invalid release key ID")
    require(isinstance(release["package_id"], str) and IDENTIFIER.fullmatch(release["package_id"]),
            "Invalid release package ID")
    require(isinstance(release["signature"], str), "Invalid release signature")
    files = release["files"]
    require(isinstance(files, dict) and 1 <= len(files) <= MAX_FILES, "Invalid release inventory")
    for name, value in files.items():
        require(member_name_ok(name), "Release path refused: paths are relative, without '..' or links")
        require(name != RELEASE_NAME, "release.json cannot list itself")
        require(isinstance(value, str) and SHA256.fullmatch(value), "Invalid release file hash")
    require(isinstance(release["snapshot"], str) and release["snapshot"] in files,
            "Snapshot is not in the signed inventory")
    return release


def check_release(root, release, trust, now):
    """Verify a release document against the files under root; the snapshot is read in historical mode."""
    validate_release(release)
    grant = trusted_grant(trust, release["key_id"])
    verify_signature(release, grant)
    require(release["package_id"] in grant["packages"], "Publisher key is not trusted for this package")
    present = scan(root)
    present.pop(RELEASE_NAME, None)
    listed = release["files"]
    missing = sorted(set(listed) - set(present))
    require(not missing, f"Release file is missing: {missing[0] if missing else ''}")
    extra = sorted(set(present) - set(listed))
    require(not extra, f"Unlisted file in release: {extra[0] if extra else ''}")
    for name in sorted(listed):
        require(file_sha256(present[name]) == listed[name], f"Release file changed: {name}")
    envelope = read_member_json(present[release["snapshot"]])
    require(isinstance(envelope, dict), "Release snapshot is not a signed envelope")
    payload, expired = resolve_historical([envelope], trust, now)
    require(payload["package_id"] == release["package_id"], "Release package identity mismatch")
    require(payload["author_id"] == grant["author_id"], "Release author mismatch")
    return {"status": "verified", "package_id": payload["package_id"], "edition_id": payload["edition_id"],
            "files_verified": len(listed), "expired": expired}


def verify_bundle(root, trust, now):
    """Signature, every listed hash, no unlisted file except the root release.json, snapshot readable."""
    root = Path(root)
    require(root.is_dir(), "Bundle directory not found")
    require(os.path.lexists(root / RELEASE_NAME), "Bundle has no release.json")
    release = read_member_json(root / RELEASE_NAME)
    require(isinstance(release, dict), "Invalid release manifest")
    return check_release(root, release, trust, now)
