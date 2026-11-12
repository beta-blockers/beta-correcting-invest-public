import json
from pathlib import Path

from public_pilot import cli

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_real_example_round_trip_and_offline_execution_barrier(tmp_path, monkeypatch, capsys):
    def no_broker():
        raise AssertionError("Offline workflow must not create a broker client")

    monkeypatch.setattr(cli, "AlpacaPaper", no_broker)
    args = ["--state", str(tmp_path / "state"), "--trust", str(EXAMPLES / "trust.json")]
    assert cli.main(args + ["verify", str(EXAMPLES / "demo.snapshot.json")]) == 0
    capsys.readouterr()
    assert cli.main(args + ["install", str(EXAMPLES / "demo.snapshot.json")]) == 0
    capsys.readouterr()
    assert cli.main(args + ["preview", "synthetic-example", "--offline", str(EXAMPLES / "account.json")]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["orders_submitted"] == 0
    assert cli.main(args + ["execute-paper", preview["plan_id"], "--account", "synthetic-offline-account"]) == 2
    assert "Offline" in capsys.readouterr().err
    assert cli.main(args + ["install", str(EXAMPLES / "demo.delta.json")]) == 0
    capsys.readouterr()
    assert cli.main(args + ["show", "synthetic-example"]) == 0
    assert json.loads(capsys.readouterr().out)["edition_id"] == "demo-2"
