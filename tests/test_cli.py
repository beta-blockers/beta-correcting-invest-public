from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path

import pytest

from conftest import FakeBroker
from public_pilot import cli
from public_pilot.common import iso, now
from support import call, write

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class LiveBroker(FakeBroker):
    """The simulated broker, observed at the moment of each snapshot, plus the close() the command calls."""

    def snapshot(self, universe):
        result = super().snapshot(universe)
        result["observed_at"] = iso(now())
        for quote in result["quotes"].values():
            quote["at"] = result["observed_at"]
        return result

    def close(self):
        pass


def test_demo_edition_previews_live_and_trades_only_with_paper_permission(tmp_path, author, payload, snapshot,
                                                                          monkeypatch, capsys):
    trust, sign = author
    started = now()  # the commands read their own clock, so the edition is current now
    payload.update(purpose="demo", published_at=iso(started - timedelta(days=1)),
                   information_cutoff=iso(started - timedelta(days=2)), valid_until=iso(started + timedelta(days=30)))
    reading = deepcopy(trust)
    reading["test-key"]["allow_paper"] = False
    edition = write(tmp_path / "edition.json", sign(payload))
    without = ["--state", tmp_path / "state", "--trust", write(tmp_path / "reading.json", reading)]
    paper = ["--state", tmp_path / "state", "--trust", write(tmp_path / "paper.json", trust)]
    monkeypatch.setattr(cli, "AlpacaPaper", lambda: pytest.fail("No broker client without paper permission"))
    code, installed = call(capsys, without + ["install", edition])
    assert code == 0 and installed["purpose"] == "demo"
    code, refusal = call(capsys, without + ["preview", "test-research"])
    assert code == 2 and refusal["reason"] == "This key is trusted only for demonstrations"
    broker = LiveBroker(snapshot)
    monkeypatch.setattr(cli, "AlpacaPaper", lambda: broker)
    code, preview = call(capsys, paper + ["preview", "test-research"])
    assert code == 0 and preview["plan"]["offline"] is False and preview["plan"]["orders"]
    execute = ["execute-paper", preview["plan_id"], "--account", "paper-test-account"]
    code, refusal = call(capsys, without + execute)
    assert code == 2 and refusal["reason"] == "This key is trusted only for demonstrations"
    assert broker.posts == 0
    code, result = call(capsys, paper + execute)
    assert code == 0 and result["status"] == "complete"
    assert broker.posts == len(preview["plan"]["orders"])


def test_real_example_round_trip_and_offline_execution_barrier(tmp_path, monkeypatch, capsys):
    def no_broker():
        raise AssertionError("Offline workflow must not create a broker client")

    monkeypatch.setattr(cli, "AlpacaPaper", no_broker)
    args = ["--state", str(tmp_path / "state"), "--trust", str(EXAMPLES / "trust.json")]
    assert cli.main(args + ["verify", str(EXAMPLES / "demo.snapshot.json")]) == 0
    capsys.readouterr()
    assert cli.main(args + ["install", str(EXAMPLES / "demo.snapshot.json")]) == 0
    capsys.readouterr()
    # The example's key is trusted without paper permission, so a live preview stops before any broker contact.
    assert cli.main(args + ["preview", "synthetic-example"]) == 2
    assert "trusted only for demonstrations" in capsys.readouterr().err
    assert cli.main(args + ["preview", "synthetic-example", "--offline", str(EXAMPLES / "account.json")]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["orders_submitted"] == 0
    assert cli.main(args + ["execute-paper", preview["plan_id"], "--account", "synthetic-offline-account"]) == 2
    assert "Offline" in capsys.readouterr().err
    assert cli.main(args + ["install", str(EXAMPLES / "demo.delta.json")]) == 0
    capsys.readouterr()
    assert cli.main(args + ["show", "synthetic-example"]) == 0
    assert json.loads(capsys.readouterr().out)["edition_id"] == "demo-2"
