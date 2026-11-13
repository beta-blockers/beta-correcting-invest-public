"""Local package provenance and durable submission intent. No research database."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import sqlite3

from .common import MAX_DOCUMENT_BYTES, Refused, canonical, digest, fields, loads, require, timestamp
from .packages import resolve_chain, resolve_historical


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        db_path = self.directory / "engine.sqlite"
        self.db = sqlite3.connect(db_path, timeout=30, isolation_level=None)
        os.chmod(db_path, 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
          PRAGMA synchronous=FULL;
          CREATE TABLE IF NOT EXISTS editions (
            package_id TEXT, edition_id TEXT, hash TEXT, proofs TEXT NOT NULL,
            PRIMARY KEY(package_id, edition_id));
          CREATE TABLE IF NOT EXISTS active (package_id TEXT PRIMARY KEY, edition_id TEXT);
          CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'preview');
          CREATE TABLE IF NOT EXISTS orders (
            plan_id TEXT, idx INTEGER, attempted INTEGER NOT NULL DEFAULT 0,
            observation TEXT, PRIMARY KEY(plan_id, idx));
        """)

    @contextmanager
    def locked(self):
        with (self.directory / "engine.lock").open("a") as lock:
            os.chmod(lock.name, 0o600)
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def close(self):
        self.db.close()

    def load_package(self, package_id, trust, instant, *, check_freshness=True, trading=False):
        row = self.db.execute("""SELECT e.* FROM editions e JOIN active a
          ON a.package_id=e.package_id AND a.edition_id=e.edition_id
          WHERE a.package_id=?""", (package_id,)).fetchone()
        require(row is not None, "Package is not installed")
        proofs = loads(row["proofs"])
        payload = resolve_chain(proofs, trust, instant, check_freshness=check_freshness, trading=trading)
        require(digest(payload) == row["hash"], "Installed package identity changed")
        return payload, proofs

    def installed(self, package_id):
        """The active edition as it was verified when it was installed. Its signatures are not checked again, so
        it serves only as the reference for the downgrade checks when its key is no longer trusted."""
        row = self.db.execute("""SELECT e.* FROM editions e JOIN active a
          ON a.package_id=e.package_id AND a.edition_id=e.edition_id
          WHERE a.package_id=?""", (package_id,)).fetchone()
        require(row is not None, "Package is not installed")
        try:
            proofs = loads(row["proofs"])
            payload = dict(proofs[0]["payload"])
            for delta in proofs[1:]:
                payload = {**payload, **delta["payload"]["replace"]}
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
            raise Refused("Installed package identity changed") from exc
        require(digest(payload) == row["hash"], "Installed package identity changed")
        return payload

    def install(self, envelope, trust, instant, *, allow_expired=False):
        fields(envelope, ("format", "kind", "key_id", "payload", "signature"))
        require(isinstance(envelope["payload"], dict), "Invalid envelope payload")
        package_id = envelope["payload"].get("package_id")
        require(isinstance(package_id, str), "Missing package ID")
        current = self.db.execute("SELECT 1 FROM active WHERE package_id=?", (package_id,)).fetchone()
        previous = None
        proofs = []
        reverified = True
        if current and envelope.get("kind") == "snapshot":
            # A snapshot replaces the installed edition, so that edition need not verify with the current trust
            # file: after a publisher key is removed, a snapshot signed with a trusted key still installs. The
            # downgrade checks below then compare with the edition as it was verified when it was installed.
            try:
                previous, _ = self.load_package(package_id, trust, instant, check_freshness=False)
            except Refused:
                previous, reverified = self.installed(package_id), False
        elif current:
            previous, proofs = self.load_package(package_id, trust, instant, check_freshness=False)
        chain = [envelope] if envelope.get("kind") == "snapshot" else proofs + [envelope]
        require(len(canonical(chain)) <= MAX_DOCUMENT_BYTES, "Chain too large; import a fresh signed snapshot")
        # Historical mode relaxes only expiry; every other check below still applies.
        payload = resolve_historical(chain, trust, instant)[0] if allow_expired else resolve_chain(chain, trust, instant)
        identity = digest(payload)
        if previous:
            if identity == digest(previous):
                if not reverified:  # the same edition, re-signed: keep the proofs that verify with this trust
                    self.db.execute("UPDATE editions SET proofs=? WHERE package_id=? AND edition_id=? AND hash=?",
                                    (canonical(chain).decode(), package_id, payload["edition_id"], identity))
                return payload
            require(timestamp(payload["published_at"]) > timestamp(previous["published_at"]) and
                    timestamp(payload["information_cutoff"]) >= timestamp(previous["information_cutoff"]) and
                    payload["author_id"] == previous["author_id"] and
                    payload["purpose"] == previous["purpose"], "Package downgrade or identity change refused")
        old = self.db.execute("SELECT hash FROM editions WHERE package_id=? AND edition_id=?",
                              (package_id, payload["edition_id"])).fetchone()
        require(old is None or old["hash"] == identity, "Existing edition cannot be replaced")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT OR IGNORE INTO editions VALUES (?,?,?,?)",
                            (package_id, payload["edition_id"], identity, canonical(chain).decode()))
            self.db.execute("INSERT OR REPLACE INTO active VALUES (?,?)", (package_id, payload["edition_id"]))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return payload

    def save_plan(self, plan):
        identity = digest(plan)
        self.db.execute("INSERT OR IGNORE INTO plans (id,body) VALUES (?,?)", (identity, canonical(plan).decode()))
        return identity

    def plan(self, identity):
        row = self.db.execute("SELECT * FROM plans WHERE id=?", (identity,)).fetchone()
        require(row is not None, "Unknown plan")
        body = loads(row["body"])
        require(digest(body) == identity, "Plan identity changed")
        return body, row["status"]

    def status(self, identity, status):
        self.db.execute("UPDATE plans SET status=? WHERE id=?", (status, identity))

    def outstanding(self, except_id=""):
        return self.db.execute("SELECT id FROM plans WHERE status='started' AND id!=?", (except_id,)).fetchall()

    def order(self, identity, idx):
        self.db.execute("INSERT OR IGNORE INTO orders (plan_id,idx) VALUES (?,?)", (identity, idx))
        return self.db.execute("SELECT * FROM orders WHERE plan_id=? AND idx=?", (identity, idx)).fetchone()

    def mark_attempt(self, identity, idx):
        # Autocommit + synchronous FULL: intent is durable BEFORE the HTTP request.
        self.db.execute("UPDATE orders SET attempted=1 WHERE plan_id=? AND idx=?", (identity, idx))

    def record(self, identity, idx, observation):
        self.db.execute("UPDATE orders SET observation=? WHERE plan_id=? AND idx=?",
                        (canonical(observation).decode(), identity, idx))
