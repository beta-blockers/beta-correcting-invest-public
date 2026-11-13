"""Explicit local commands. Import/view/preview never place orders."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from . import authoring, catalog, evaluation, newsconfig
from .broker import AlpacaPaper
from .bundles import RELEASE_NAME, verify_bundle
from .common import Refused, digest, iso, now, read_json, require, timestamp
from .execution import cancel, execute
from .packages import resolve_chain, resolve_historical, validate_payload
from .planning import Limits, build_plan
from .state import Store

# The command line's limits for a paper account, in USD: plan for up to 100,000 of it, with at most 50,000 in any
# one order (one share must fit in a single order) and 100,000 of buys and sells in all.
DEFAULT_ALLOCATION = "100000"
DEFAULT_MAX_ORDER = "50000"
DEFAULT_MAX_TURNOVER = "100000"


def parser():
    result = argparse.ArgumentParser(description="Load completed research and preview or execute a paper portfolio")
    result.add_argument("--state", default=".state", help="Private local state directory")
    result.add_argument("--trust", default="trust.json", help="Local trusted publisher public keys")
    sub = result.add_subparsers(dest="command", required=True)
    for name in ("verify", "install"):
        command = sub.add_parser(name)
        command.add_argument("file")
        command.add_argument("--allow-expired", action="store_true",
                             help="Historical mode: accept an expired edition for reading; it can never trade")
    sub.add_parser("show").add_argument("package_id")
    preview = sub.add_parser("preview")
    preview.add_argument("package_id")
    preview.add_argument("--offline", metavar="FILE", help="Synthetic observation file; result cannot execute")
    preview.add_argument("--allocation", default=DEFAULT_ALLOCATION,
                         help="USD of the paper account to plan for, never more than its equity (default %(default)s)")
    preview.add_argument("--max-order", default=DEFAULT_MAX_ORDER,
                         help="Largest single order in USD. One share must fit in an order, so this is also the "
                              "highest share price a plan can buy (default %(default)s)")
    preview.add_argument("--max-turnover", default=DEFAULT_MAX_TURNOVER,
                         help="Largest total of buys and sells in one plan, in USD (default %(default)s)")
    preview.add_argument("--max-weight", default="0.5")
    for name in ("execute-paper", "cancel-paper"):
        command = sub.add_parser(name)
        command.add_argument("plan_id")
        command.add_argument("--account", required=True, help="Exact paper account ID shown in the preview")
    sub.add_parser("status").add_argument("plan_id")
    tool_parsers(sub)
    return result


def tool_parsers(sub):
    """Offline author and reader tools. None opens the state store or contacts a broker."""
    command = sub.add_parser("keygen", help="Create a raw Ed25519 signing key outside any Git checkout")
    command.add_argument("--out", required=True, help="New key file; never overwritten")
    sub.add_parser("fingerprint", help="SHA-256 fingerprint of a base64 public key").add_argument("public_key")
    command = sub.add_parser("validate", help="Validate an unsigned payload exactly as install does")
    command.add_argument("payload")
    command.add_argument("--as-of", help="Validation instant (default: now)")
    key = argparse.ArgumentParser(add_help=False)
    key.add_argument("--key", required=True, help="Raw 32-byte Ed25519 private key file outside any Git checkout")
    key.add_argument("--key-id", required=True, help="Key ID that readers' trust files and the catalog list")
    kinds = sub.add_parser("sign", help="Sign a snapshot, a delta or a release inventory").add_subparsers(
        dest="kind", required=True)
    command = kinds.add_parser("snapshot", parents=[key])
    command.add_argument("payload")
    command.add_argument("output")
    command.add_argument("--as-of", help="Self-check instant for an already expired demo edition")
    command = kinds.add_parser("delta", parents=[key])
    command.add_argument("base", help="Unsigned payload of the previous edition")
    command.add_argument("payload", help="Unsigned payload of the new edition")
    command.add_argument("output")
    command.add_argument("--as-of", help="Self-check instant for an already expired demo edition")
    command = kinds.add_parser("release", parents=[key])
    command.add_argument("directory")
    command.add_argument("snapshot", help="Path of the signed snapshot, relative to the directory")
    sub.add_parser("verify-bundle", help="Verify a signed release inventory").add_argument("directory")
    command = sub.add_parser("sign-evaluation", parents=[key], help="Sign an evaluation bound to a snapshot")
    command.add_argument("evaluation", help="Unsigned evaluation payload")
    command.add_argument("output")
    command.add_argument("--snapshot", required=True, help="The edition's signed snapshot, signed with the same key")
    command = sub.add_parser("verify-evaluation", help="Verify a signed evaluation against its snapshot")
    command.add_argument("file")
    command.add_argument("--snapshot", required=True, help="The edition's signed snapshot")
    sub.add_parser("render-evaluation", help="Print an evaluation as a Markdown report").add_argument("file")
    actions = sub.add_parser("catalog", help="Check the catalog or build a trust file from it").add_subparsers(
        dest="action", required=True)
    command = actions.add_parser("check", help="Check the catalog and every edition under history/")
    command.add_argument("directory", nargs="?", default=".", help="Repository root (default: .)")
    command.add_argument("--base", metavar="DIR",
                         help="The base branch's tree; enforce that catalog/authors.json and history/ only append to it")
    command = actions.add_parser("trust", help="Write an engine trust file for one product")
    command.add_argument("directory", nargs="?", default=".", help="Repository root (default: .)")
    command.add_argument("--product", required=True)
    command.add_argument("--out", required=True, help="New trust file; never overwritten")
    command.add_argument("--allow-paper", action="store_true", help="Allow paper trading for active keys")
    command = sub.add_parser("resign-edition", parents=[key],
                             help="Copy a history edition to a new directory, re-signed with another key")
    command.add_argument("directory", help="Edition directory, history/<product_id>/<YYYY-QN>")
    command.add_argument("output", help="New directory for the re-signed copy; never overwritten")
    actions = sub.add_parser("history", help="Maintain the public history index").add_subparsers(
        dest="action", required=True)
    command = actions.add_parser("index", help="Regenerate history/INDEX.md")
    command.add_argument("directory", nargs="?", default=".", help="Repository root (default: .)")
    command.add_argument("--check", action="store_true", help="Fail if the committed index differs")
    command = sub.add_parser("validate-news-config", help="Validate a news addon configuration")
    command.add_argument("file")
    command.add_argument("--payload", metavar="FILE", help="Unsigned payload of the edition it monitors")


def run_keygen(args):
    return authoring.keygen(args.out)


def run_fingerprint(args):
    return {"public_key": args.public_key, "fingerprint_sha256": authoring.fingerprint(args.public_key)}


def run_validate(args):
    payload = read_json(args.payload)
    validate_payload(payload, timestamp(args.as_of) if args.as_of else now())
    return {"status": "valid", "package_id": payload["package_id"], "edition_id": payload["edition_id"],
            "sha256": digest(payload)}


def run_sign(args):
    private = authoring.load_private_key(args.key)
    if args.kind == "release":
        release = authoring.sign_release(private, args.key_id, args.directory, args.snapshot, now())
        output = authoring.write_new(Path(args.directory) / RELEASE_NAME, release)
        return {"status": "signed", "kind": "release", "output": output, "package_id": release["package_id"],
                "files": len(release["files"])}
    payload = read_json(args.payload)
    if args.kind == "snapshot":
        document = authoring.sign_snapshot(private, args.key_id, payload, now(), args.as_of)
    else:
        document = authoring.sign_delta(private, args.key_id, read_json(args.base), payload, now(), args.as_of)
    return {"status": "signed", "kind": args.kind, "output": authoring.write_new(args.output, document),
            "package_id": payload["package_id"], "edition_id": payload["edition_id"], "sha256": digest(payload)}


def run_verify_bundle(args):
    return verify_bundle(args.directory, read_json(args.trust), now())


def run_sign_evaluation(args):
    private = authoring.load_private_key(args.key)
    payload = read_json(args.evaluation)
    document = authoring.sign_evaluation(private, args.key_id, payload, read_json(args.snapshot), now())
    return {"status": "signed", "kind": "evaluation", "output": authoring.write_new(args.output, document),
            "package_id": payload["package_id"], "edition_id": payload["edition_id"]}


def run_verify_evaluation(args):
    return evaluation.verify_evaluation(read_json(args.file), read_json(args.snapshot), read_json(args.trust), now())


def run_render_evaluation(args):
    return evaluation.render(read_json(args.file))


def run_catalog(args):
    if args.action == "trust":
        return catalog.write_trust(args.directory, args.product, args.out, args.allow_paper)
    return catalog.check(args.directory, now(), args.base)


def run_resign_edition(args):
    private = authoring.load_private_key(args.key)
    return catalog.resign_edition(args.directory, args.output, private, args.key_id, now())


def run_history(args):
    return catalog.history_index(args.directory, now(), check_only=args.check)


def run_validate_news_config(args):
    payload = read_json(args.payload) if args.payload else None
    return newsconfig.validate_news_config(read_json(args.file), payload)


TOOLS = {"keygen": run_keygen, "fingerprint": run_fingerprint, "validate": run_validate, "sign": run_sign,
         "verify-bundle": run_verify_bundle, "sign-evaluation": run_sign_evaluation,
         "verify-evaluation": run_verify_evaluation, "render-evaluation": run_render_evaluation,
         "catalog": run_catalog, "resign-edition": run_resign_edition, "history": run_history,
         "validate-news-config": run_validate_news_config}


def run(args):
    if args.command in TOOLS:
        try:
            return TOOLS[args.command](args)
        except OverflowError as exc:  # e.g. a timestamp whose UTC conversion leaves the supported years
            raise Refused("Date or time out of range") from exc
    store = Store(args.state)
    broker = None
    try:
        with store.locked():
            if args.command == "status":
                plan, status = store.plan(args.plan_id)
                rows = store.db.execute("SELECT idx,attempted,observation FROM orders WHERE plan_id=? ORDER BY idx",
                                        (args.plan_id,)).fetchall()
                return {"plan_id": args.plan_id, "status": status, "plan": plan,
                        "orders": [dict(r) for r in rows]}
            # Cancellation must remain available after a publisher key is removed.
            trust = {} if args.command == "cancel-paper" else read_json(args.trust)
            instant = now()
            if args.command in ("verify", "install"):
                envelope = read_json(args.file)
                require(isinstance(envelope, dict), "Expected a signed envelope")
                if args.command == "install":
                    payload = store.install(envelope, trust, instant, allow_expired=args.allow_expired)
                    expired = args.allow_expired and instant >= timestamp(payload["valid_until"])
                else:
                    chain = []
                    if envelope.get("kind") == "delta":
                        _, chain = store.load_package(envelope["payload"]["package_id"], trust, instant,
                                                      check_freshness=False)
                    if args.allow_expired:
                        payload, expired = resolve_historical(chain + [envelope], trust, instant)
                    else:
                        payload, expired = resolve_chain(chain + [envelope], trust, instant), False
                return {"status": "installed" if args.command == "install" else "verified",
                        "package_id": payload["package_id"], "edition_id": payload["edition_id"],
                        "sha256": digest(payload), "purpose": payload["purpose"], "expired": expired}
            if args.command == "show":
                payload, _ = store.load_package(args.package_id, trust, instant, check_freshness=False)
                return payload
            if args.command == "preview":
                unresolved = [row["id"] for row in store.outstanding()]
                require(not unresolved, "Reconcile or cancel the outstanding execution first: plan " +
                        ", ".join(unresolved))
                # Offline plans can never execute, so they may read an expired edition with any trusted key.
                # A live plan can: it needs a current edition and paper permission, whatever the purpose.
                live = not args.offline
                payload, _ = store.load_package(args.package_id, trust, instant, check_freshness=live, trading=live)
                if args.offline:
                    snapshot = read_json(args.offline)
                    # Explicit offline simulation advances only the fixture clock.
                    # The resulting plan is permanently marked non-executable.
                    snapshot["observed_at"] = iso(instant)
                    for quote in snapshot["quotes"].values():
                        quote["at"] = iso(instant)
                else:
                    broker = AlpacaPaper()
                    snapshot = broker.snapshot(payload["universe"])
                limits = Limits(allocation_usd=args.allocation, max_order_usd=args.max_order,
                                max_turnover_usd=args.max_turnover, max_position_weight=args.max_weight)
                # Recheck package freshness after network observation.
                instant = now()
                payload, _ = store.load_package(args.package_id, trust, instant, check_freshness=live, trading=live)
                plan = build_plan(payload, snapshot, limits, instant, offline=bool(args.offline))
                return {"plan_id": store.save_plan(plan), "plan": plan, "orders_submitted": 0}
            plan, _ = store.plan(args.plan_id)
            require(args.account == plan["account_id"], "Explicit account confirmation does not match the plan")
            require(not plan["offline"], "Offline previews cannot contact the broker")
            broker = AlpacaPaper()
            if args.command == "execute-paper":
                return execute(store, args.plan_id, broker, trust)
            return cancel(store, args.plan_id, broker)
    finally:
        if broker:
            broker.close()
        store.close()


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        output = run(args)
    except (Refused, OSError, KeyError, TypeError, ValueError, sqlite3.Error) as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    if isinstance(output, str):  # Markdown from render-evaluation; every other command prints JSON.
        print(output, end="")
        return 0
    print(json.dumps(output, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
