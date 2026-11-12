"""Historical mode: expired editions can be read, never traded."""
import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from conftest import AT, FakeBroker, delta_for
from public_pilot import cli
from public_pilot.common import Refused, iso
from public_pilot.execution import execute
from public_pilot.packages import resolve_chain, resolve_historical
from public_pilot.planning import Limits, build_plan
from public_pilot.state import Store

# The fixture payload is valid from AT - 2 days until AT + 30 days.
LATER = AT + timedelta(days=60)
BEFORE = AT - timedelta(days=2, seconds=1)


def write(path, document):
    path.write_text(json.dumps(document))
    return str(path)


def clock(monkeypatch, *instants):
    """Freeze the CLI clock; successive calls return successive instants."""
    queue = list(instants)
    monkeypatch.setattr(cli, "now", lambda: queue.pop(0) if len(queue) > 1 else queue[0])


def no_broker():
    raise AssertionError("This command must not create a broker client")


class ClosingBroker(FakeBroker):
    """The simulated broker, plus the close() the command calls when it finishes."""

    def close(self):
        pass


def call(capsys, argv):
    code = cli.main(argv)
    captured = capsys.readouterr()
    return code, json.loads(captured.out if code == 0 else captured.err)


@pytest.fixture
def cli_env(tmp_path, author, monkeypatch):
    trust, sign = author
    monkeypatch.setattr(cli, "AlpacaPaper", no_broker)
    base = ["--state", str(tmp_path / "state"), "--trust", write(tmp_path / "trust.json", trust)]
    return base, sign, tmp_path


# resolve_historical ---------------------------------------------------------

def test_historical_mode_reads_an_expired_edition_that_normal_mode_refuses(author, payload):
    trust, sign = author
    assert resolve_historical([sign(payload)], trust, LATER) == (payload, True)
    with pytest.raises(Refused, match="Expired or future-dated research"):
        resolve_chain([sign(payload)], trust, LATER)


def test_historical_mode_reports_current_editions_and_exclusive_expiry(author, payload):
    trust, sign = author
    assert resolve_historical([sign(payload)], trust, AT) == (payload, False)
    expiry = AT + timedelta(days=30)
    assert resolve_historical([sign(payload)], trust, expiry - timedelta(microseconds=1))[1] is False
    assert resolve_historical([sign(payload)], trust, expiry)[1] is True


def test_historical_mode_refuses_future_dated_research(author, payload):
    trust, sign = author
    with pytest.raises(Refused, match="^Future-dated research$"):
        resolve_historical([sign(payload)], trust, BEFORE)


def test_historical_mode_resolves_an_expired_delta_chain(author, payload):
    trust, sign = author
    delta = delta_for(payload, edition_id="edition-2", published_at=iso(AT - timedelta(days=1)))
    resolved, expired = resolve_historical([sign(payload), sign(delta, "delta")], trust, LATER)
    assert resolved["edition_id"] == "edition-2" and expired is True
    delta["result_sha256"] = "0" * 64
    with pytest.raises(Refused, match="result hash"):
        resolve_historical([sign(payload), sign(delta, "delta")], trust, LATER)


# verify / install --allow-expired ----------------------------------------------

@pytest.mark.parametrize("command", ["verify", "install"])
def test_allow_expired_flag_reads_expired_editions_and_reports_expiry(cli_env, payload, monkeypatch, capsys, command):
    base, sign, tmp_path = cli_env
    edition = write(tmp_path / "edition.json", sign(payload))
    clock(monkeypatch, LATER)
    code, refusal = call(capsys, base + [command, edition])
    assert code == 2 and refusal == {"status": "refused", "reason": "Expired or future-dated research"}
    code, output = call(capsys, base + [command, edition, "--allow-expired"])
    assert code == 0 and output["expired"] is True and output["edition_id"] == "edition-1"


@pytest.mark.parametrize("flag", [[], ["--allow-expired"]])
@pytest.mark.parametrize("command", ["verify", "install"])
def test_current_editions_report_not_expired_with_or_without_the_flag(cli_env, payload, monkeypatch, capsys,
                                                                      command, flag):
    base, sign, tmp_path = cli_env
    clock(monkeypatch, AT)
    code, output = call(capsys, base + [command, write(tmp_path / "edition.json", sign(payload))] + flag)
    assert code == 0 and output["expired"] is False
    assert set(output) == {"status", "package_id", "edition_id", "sha256", "purpose", "expired"}


@pytest.mark.parametrize("command", ["verify", "install"])
@pytest.mark.parametrize("flag", [[], ["--allow-expired"]])
def test_future_dated_editions_are_refused_in_both_modes(cli_env, payload, monkeypatch, capsys, command, flag):
    base, sign, tmp_path = cli_env
    clock(monkeypatch, BEFORE)
    code, refusal = call(capsys, base + [command, write(tmp_path / "edition.json", sign(payload))] + flag)
    assert code == 2 and "future-dated research" in refusal["reason"].lower()


def test_verify_allow_expired_applies_a_delta_to_the_installed_base(cli_env, payload, monkeypatch, capsys):
    base, sign, tmp_path = cli_env
    clock(monkeypatch, LATER)
    assert call(capsys, base + ["install", write(tmp_path / "base.json", sign(payload)), "--allow-expired"])[0] == 0
    delta = delta_for(payload, edition_id="edition-2", published_at=iso(AT - timedelta(days=1)))
    code, output = call(capsys, base + ["verify", write(tmp_path / "delta.json", sign(delta, "delta")),
                                        "--allow-expired"])
    assert code == 0 and output["edition_id"] == "edition-2" and output["expired"] is True


# Store.install(allow_expired=True) keeps every other check --------------------

def test_store_installs_expired_edition_only_with_keyword(store, author, payload):
    trust, sign = author
    with pytest.raises(Refused, match="Expired"):
        store.install(sign(payload), trust, LATER)
    assert store.install(sign(payload), trust, LATER, allow_expired=True) == payload
    assert store.load_package(payload["package_id"], trust, LATER, check_freshness=False)[0] == payload
    with pytest.raises(Refused, match="Expired"):
        store.load_package(payload["package_id"], trust, LATER)


MODES = [pytest.param(False, AT, id="normal"), pytest.param(True, AT, id="historical-current"),
         pytest.param(True, LATER, id="historical-expired")]


@pytest.mark.parametrize("allow_expired, instant", MODES)
def test_signature_is_checked_in_both_modes(store, author, payload, allow_expired, instant):
    trust, sign = author
    envelope = sign(payload)
    envelope["payload"]["research"] = "Altered after signing."
    with pytest.raises(Refused, match="signature"):
        store.install(envelope, trust, instant, allow_expired=allow_expired)


@pytest.mark.parametrize("allow_expired, instant", MODES)
def test_trust_scope_for_package_author_and_paper_applies_in_both_modes(store, author, payload,
                                                                        allow_expired, instant):
    trust, sign = author
    for change, message in ((("packages", ["another-package"]), "not trusted"),
                            (("author_id", "another-author"), "author mismatch"),
                            (("allow_paper", False), "demonstrations")):
        narrowed = deepcopy(trust)
        narrowed["test-key"][change[0]] = change[1]
        with pytest.raises(Refused, match=message):
            store.install(sign(payload), narrowed, instant, allow_expired=allow_expired)
    with pytest.raises(Refused, match="not in the local trust store"):
        store.install(sign(payload), {}, instant, allow_expired=allow_expired)


@pytest.mark.parametrize("allow_expired, instant", MODES)
def test_downgrade_and_identity_checks_apply_in_both_modes(store, author, payload, allow_expired, instant):
    trust, sign = author
    newer = {**payload, "edition_id": "edition-2", "published_at": iso(AT - timedelta(days=1))}
    store.install(sign(newer), trust, instant, allow_expired=allow_expired)
    with pytest.raises(Refused, match="downgrade"):
        store.install(sign(payload), trust, instant, allow_expired=allow_expired)
    backwards = {**payload, "edition_id": "edition-3", "published_at": iso(AT - timedelta(hours=1)),
                 "information_cutoff": iso(AT - timedelta(days=4))}
    with pytest.raises(Refused, match="downgrade"):
        store.install(sign(backwards), trust, instant, allow_expired=allow_expired)
    demo = {**payload, "edition_id": "edition-4", "published_at": iso(AT - timedelta(hours=1)), "purpose": "demo"}
    with pytest.raises(Refused, match="identity change"):
        store.install(sign(demo), trust, instant, allow_expired=allow_expired)
    rewrite = {**newer, "published_at": iso(AT - timedelta(hours=1)), "research": "Rewritten."}
    with pytest.raises(Refused, match="Existing edition cannot be replaced"):
        store.install(sign(rewrite), trust, instant, allow_expired=allow_expired)
    assert store.load_package(payload["package_id"], trust, instant, check_freshness=False)[0] == newer


def test_expired_edition_cannot_replace_a_newer_installed_edition(cli_env, payload, monkeypatch, capsys):
    base, sign, tmp_path = cli_env
    newer = {**payload, "edition_id": "edition-2", "published_at": iso(AT - timedelta(days=1))}
    older = {**payload, "valid_until": iso(AT - timedelta(hours=1))}
    clock(monkeypatch, AT)
    assert call(capsys, base + ["install", write(tmp_path / "newer.json", sign(newer))])[0] == 0
    code, refusal = call(capsys, base + ["install", write(tmp_path / "older.json", sign(older)), "--allow-expired"])
    assert code == 2 and "downgrade" in refusal["reason"]
    code, shown = call(capsys, base + ["show", "test-research"])
    assert code == 0 and shown["edition_id"] == "edition-2"


# preview --offline reads expired editions; live preview and execution do not ------

@pytest.fixture
def expired_install(cli_env, payload, snapshot, monkeypatch, capsys):
    base, sign, tmp_path = cli_env
    clock(monkeypatch, LATER)
    assert call(capsys, base + ["install", write(tmp_path / "edition.json", sign(payload)), "--allow-expired"])[0] == 0
    return base, write(tmp_path / "account.json", snapshot)


def test_offline_preview_of_expired_edition_is_never_executable(expired_install, monkeypatch, capsys):
    base, account = expired_install
    clock(monkeypatch, LATER)
    code, preview = call(capsys, base + ["preview", "test-research", "--offline", account])
    assert code == 0 and preview["plan"]["offline"] is True and preview["orders_submitted"] == 0
    assert preview["plan"]["orders"]
    code, refusal = call(capsys, base + ["execute-paper", preview["plan_id"], "--account", "paper-test-account"])
    assert code == 2 and "Offline" in refusal["reason"]


def test_live_preview_refuses_an_expired_edition(expired_install, monkeypatch, capsys):
    base, _ = expired_install
    clock(monkeypatch, LATER)
    code, refusal = call(capsys, base + ["preview", "test-research"])
    assert code == 2 and refusal["reason"] == "Expired or future-dated research"


def test_live_preview_rechecks_freshness_after_observation(cli_env, payload, snapshot, monkeypatch, capsys):
    base, sign, tmp_path = cli_env
    clock(monkeypatch, AT)
    assert call(capsys, base + ["install", write(tmp_path / "edition.json", sign(payload))])[0] == 0
    monkeypatch.setattr(cli, "AlpacaPaper", lambda: ClosingBroker(snapshot))
    clock(monkeypatch, AT, LATER)  # expires between the two package loads
    code, refusal = call(capsys, base + ["preview", "test-research"])
    assert code == 2 and refusal["reason"] == "Expired or future-dated research"
    clock(monkeypatch, AT)
    code, preview = call(capsys, base + ["preview", "test-research"])
    assert code == 0 and preview["plan"]["offline"] is False


def test_execution_submits_no_new_order_for_an_expired_edition(store, author, payload, snapshot):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    identity = store.save_plan(build_plan(payload, snapshot, Limits(), AT))
    broker = FakeBroker(snapshot)
    with pytest.raises(Refused, match="Expired or future-dated research"):
        execute(store, identity, broker, trust, clock=lambda: LATER)
    assert broker.posts == 0


def test_historically_installed_edition_cannot_submit_orders(store, author, payload, snapshot):
    trust, sign = author
    store.install(sign(payload), trust, LATER, allow_expired=True)
    snapshot = deepcopy(snapshot)
    snapshot["observed_at"] = iso(LATER)
    for quote in snapshot["quotes"].values():
        quote["at"] = iso(LATER)
    identity = store.save_plan(build_plan(payload, snapshot, Limits(), LATER))
    broker = FakeBroker(snapshot)
    with pytest.raises(Refused, match="Expired or future-dated research"):
        execute(store, identity, broker, trust, clock=lambda: LATER)
    assert broker.posts == 0


def test_execute_paper_command_submits_no_order_once_research_expired(tmp_path, author, payload, snapshot,
                                                                      monkeypatch, capsys):
    # Dates before the real clock, so the command's own clock sees an expired edition.
    trust, sign = author
    then = datetime(2020, 1, 2, 15, tzinfo=timezone.utc)
    payload.update(published_at=iso(then - timedelta(days=1)), information_cutoff=iso(then - timedelta(days=2)),
                   valid_until=iso(then + timedelta(days=30)))
    snapshot = deepcopy(snapshot)
    snapshot["observed_at"] = iso(then)
    for quote in snapshot["quotes"].values():
        quote["at"] = iso(then)
    state = Store(tmp_path / "state")
    try:
        state.install(sign(payload), trust, then)
        identity = state.save_plan(build_plan(payload, snapshot, Limits(), then))
    finally:
        state.close()
    broker = ClosingBroker(snapshot)
    monkeypatch.setattr(cli, "AlpacaPaper", lambda: broker)
    argv = ["--state", str(tmp_path / "state"), "--trust", write(tmp_path / "trust.json", trust),
            "execute-paper", identity, "--account", "paper-test-account"]
    code, refusal = call(capsys, argv)
    assert code == 2 and refusal["reason"] == "Expired or future-dated research"
    assert broker.posts == 0
