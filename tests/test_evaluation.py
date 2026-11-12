"""Signed evaluation documents: sign-evaluation, verify-evaluation and render-evaluation."""
from copy import deepcopy
import json
from datetime import timedelta

import pytest

from conftest import AT
from public_pilot import authoring, cli
from public_pilot.common import Refused, digest
from public_pilot.evaluation import render, verify_evaluation
from support import call, freeze, new_key, trust_for, write

KEY_ID = "test-key"
LATER = AT + timedelta(days=60)


@pytest.fixture
def signer(tmp_path):
    directory = tmp_path / "keys"
    directory.mkdir(mode=0o700)
    private, created = new_key(directory)
    return private, created["key"]


@pytest.fixture
def trust(signer):
    return trust_for(signer[0], KEY_ID, "test-author", ["test-research"], allow_paper=True)


@pytest.fixture
def snapshot(signer, payload):
    return authoring.sign_snapshot(signer[0], KEY_ID, payload, AT)


def scores(payload, **changes):
    """A fictional evaluation of the conftest payload (DEMOA and DEMOB at 0.4 each)."""
    return {"package_id": payload["package_id"], "edition_id": payload["edition_id"],
            "author_id": payload["author_id"], "package_sha256": digest(payload),
            "as_of": payload["information_cutoff"],
            "method": {"name": "Fictional two-pillar score", "version": "1.0",
                       "description": "Invented for tests."},
            "thresholds": {"include_min": "50"},
            "companies": {
                "DEMOA": {"rank": 1, "composite": "72.5", "components": {"p1": "80", "p2": "65"},
                          "decision": "include", "weight": "0.4", "note": ""},
                "DEMOB": {"rank": 2, "composite": "61", "components": {"p1": "60", "p2": "62"},
                          "decision": "include", "weight": "0.40", "note": "Fictional note."}},
            "defaults_disclosed": ["p2 for DEMOB uses the neutral default 50 (fictional)."], **changes}


def signed(signer, evaluation):
    """Sign without the signer's self-check, so that broken evaluations can be tested."""
    return authoring.sign(signer[0], {"format": "public-pilot-evaluation-v1", "key_id": KEY_ID,
                                      "payload": evaluation})


def company(payload, symbol, **changes):
    evaluation = scores(payload)
    evaluation["companies"][symbol].update(changes)
    return evaluation


def test_valid_evaluation_verifies_on_the_command_line(tmp_path, signer, trust, snapshot, payload,
                                                       monkeypatch, capsys):
    freeze(monkeypatch, AT)
    files = [write(tmp_path / "evaluation.json", signed(signer, scores(payload))), "--snapshot",
             write(tmp_path / "snapshot.json", snapshot)]
    code, output = call(capsys, ["--trust", write(tmp_path / "trust.json", trust), "verify-evaluation"] + files)
    assert code == 0 and output == {"status": "verified", "package_id": "test-research", "edition_id": "edition-1",
                                    "package_sha256": digest(payload), "companies": 2, "expired": False}


def test_expired_snapshot_verifies_with_expired_true(signer, trust, snapshot, payload):
    result = verify_evaluation(signed(signer, scores(payload)), snapshot, trust, LATER)
    assert result["expired"] is True
    with pytest.raises(Refused, match="Future-dated research"):
        verify_evaluation(signed(signer, scores(payload)), snapshot, trust, AT - timedelta(days=3))


def test_mismatched_hash_is_refused(signer, trust, snapshot, payload):
    with pytest.raises(Refused, match="package_sha256 mismatch"):
        verify_evaluation(signed(signer, scores(payload, package_sha256="0" * 64)), snapshot, trust, AT)
    other = {**payload, "research": "A different edition text."}
    with pytest.raises(Refused, match="package_sha256 mismatch"):
        verify_evaluation(signed(signer, scores(payload, package_sha256=digest(other))), snapshot, trust, AT)


@pytest.mark.parametrize("name, value", [("package_id", "other-package"), ("edition_id", "other-edition"),
                                         ("author_id", "other-author")])
def test_identifiers_must_match_the_snapshot(tmp_path, signer, snapshot, payload, name, value):
    other, _ = new_key(tmp_path / "keys", "other.key")
    trust = {**trust_for(signer[0], KEY_ID, "test-author", ["test-research", "other-package"], allow_paper=True),
             **trust_for(other, "other-key", "other-author", ["test-research"])}
    key, key_id = (other, "other-key") if name == "author_id" else (signer[0], KEY_ID)
    document = authoring.sign(key, {"format": "public-pilot-evaluation-v1", "key_id": key_id,
                                    "payload": scores(payload, **{name: value})})
    with pytest.raises(Refused, match=f"Evaluation {name} does not match the snapshot"):
        verify_evaluation(document, snapshot, trust, AT)


def test_companies_must_equal_the_universe(signer, trust, snapshot, payload):
    missing = scores(payload)
    del missing["companies"]["DEMOB"]
    extra = scores(payload)
    extra["companies"]["DEMOC"] = {**extra["companies"]["DEMOB"], "rank": 3, "composite": "1", "weight": "0"}
    for evaluation in (missing, extra):
        with pytest.raises(Refused, match="equal the snapshot universe"):
            verify_evaluation(signed(signer, evaluation), snapshot, trust, AT)


def test_weights_equal_the_payload_targets_or_zero(signer, trust, payload):
    payload = {**payload, "universe": ["DEMOA", "DEMOB", "DEMOC"]}
    snapshot = authoring.sign_snapshot(signer[0], KEY_ID, payload, AT)
    evaluation = scores(payload)
    evaluation["companies"]["DEMOC"] = {"rank": 3, "composite": "10", "components": {}, "decision": "exit",
                                        "weight": "0", "note": "Kept in the universe so it can be sold."}
    assert verify_evaluation(signed(signer, evaluation), snapshot, trust, AT)["companies"] == 3
    wrong_target = deepcopy(evaluation)
    wrong_target["companies"]["DEMOA"]["weight"] = "0.45"
    untargeted = deepcopy(evaluation)
    untargeted["companies"]["DEMOC"]["weight"] = "0.1"
    for bad, symbol in ((wrong_target, "DEMOA"), (untargeted, "DEMOC")):
        with pytest.raises(Refused, match=f"weight for {symbol} differs from the payload target"):
            verify_evaluation(signed(signer, bad), snapshot, trust, AT)


@pytest.mark.parametrize("ranks, composites", [
    ((1, 1), ("72.5", "61")), ((1, 3), ("72.5", "61")), ((0, 1), ("72.5", "61")),
    ((2, 1), ("72.5", "61")), ((1, 2), ("61", "72.5")),
])
def test_ranks_are_a_permutation_in_descending_composite_order(signer, trust, snapshot, payload, ranks, composites):
    evaluation = scores(payload)
    for symbol, rank, composite in zip(("DEMOA", "DEMOB"), ranks, composites):
        evaluation["companies"][symbol].update(rank=rank, composite=composite)
    with pytest.raises(Refused, match="rank"):
        verify_evaluation(signed(signer, evaluation), snapshot, trust, AT)


def test_tied_composites_may_be_ranked_either_way(signer, trust, snapshot, payload):
    evaluation = scores(payload)
    evaluation["companies"]["DEMOB"]["composite"] = "72.50"
    assert verify_evaluation(signed(signer, evaluation), snapshot, trust, AT)["status"] == "verified"


def test_at_most_forty_components_per_company(signer, trust, snapshot, payload):
    forty = {f"c{i}": "1" for i in range(40)}
    assert verify_evaluation(signed(signer, company(payload, "DEMOA", components=forty)), snapshot, trust, AT)
    with pytest.raises(Refused, match="At most 40 components"):
        verify_evaluation(signed(signer, company(payload, "DEMOA", components={**forty, "c40": "1"})),
                          snapshot, trust, AT)


@pytest.mark.parametrize("field, value", [
    ("composite", 72), ("composite", 72.5), ("composite", "1e3"), ("composite", "NaN"), ("composite", " 72"),
    ("composite", "+72"), ("composite", "072"), ("composite", ".5"), ("components", {"p1": 80}),
    ("weight", 0.4), ("weight", "1.5"), ("weight", "-0.1"), ("rank", 1.0), ("rank", "1"), ("rank", True),
])
def test_numbers_are_decimal_strings_and_ranks_are_integers(signer, trust, snapshot, payload, field, value):
    with pytest.raises(Refused):
        verify_evaluation(signed(signer, company(payload, "DEMOA", **{field: value})), snapshot, trust, AT)


def test_threshold_values_are_decimal_strings(signer, trust, snapshot, payload):
    with pytest.raises(Refused, match="threshold"):
        verify_evaluation(signed(signer, scores(payload, thresholds={"include_min": 50})), snapshot, trust, AT)


@pytest.mark.parametrize("evaluation_change", [
    {"method": {"name": "x" * 201, "version": "1", "description": ""}},
    {"method": {"name": "", "version": "1", "description": ""}},
    {"method": {"name": "n", "version": "v" * 51, "description": ""}},
    {"method": {"name": "n", "version": "1", "description": "d" * 20_001}},
    {"defaults_disclosed": ["d" * 1_001]},
    {"defaults_disclosed": [""]},
])
def test_text_is_length_limited(signer, trust, snapshot, payload, evaluation_change):
    with pytest.raises(Refused, match="Invalid evaluation"):
        verify_evaluation(signed(signer, scores(payload, **evaluation_change)), snapshot, trust, AT)
    with pytest.raises(Refused, match="note"):
        verify_evaluation(signed(signer, company(payload, "DEMOA", note="n" * 2_001)), snapshot, trust, AT)


def test_unknown_members_are_refused_at_every_level(signer, trust, snapshot, payload):
    method = scores(payload)
    method["method"]["prompt"] = "not allowed"
    member = company(payload, "DEMOA", sector="not allowed")
    for document in (signed(signer, scores(payload, extra=True)), signed(signer, method), signed(signer, member),
                     {**signed(signer, scores(payload)), "reviewer": "none"}):
        with pytest.raises(Refused, match="Missing or unknown document fields"):
            verify_evaluation(document, snapshot, trust, AT)
    with pytest.raises(Refused, match="Unknown evaluation decision"):
        verify_evaluation(signed(signer, company(payload, "DEMOA", decision="buy")), snapshot, trust, AT)


def test_strict_json_is_required(tmp_path, signer, trust, snapshot, payload, monkeypatch, capsys):
    freeze(monkeypatch, AT)
    text = write(tmp_path / "evaluation.json", signed(signer, scores(payload)))
    raw = open(text).read().replace('"format"', '"format": "duplicate",\n  "format"', 1)
    open(text, "w").write(raw)
    code, refusal = call(capsys, ["--trust", write(tmp_path / "trust.json", trust), "verify-evaluation", text,
                                  "--snapshot", write(tmp_path / "snapshot.json", snapshot)])
    assert code == 2 and refusal["reason"] == "Invalid JSON document"  # the strict parser's duplicate-key refusal


def test_wrong_key_is_refused(tmp_path, signer, trust, snapshot, payload):
    other, _ = new_key(tmp_path / "keys", "other.key")
    forged = authoring.sign(other, {"format": "public-pilot-evaluation-v1", "key_id": KEY_ID,
                                    "payload": scores(payload)})
    with pytest.raises(Refused, match="signature"):
        verify_evaluation(forged, snapshot, trust, AT)
    unknown = authoring.sign(other, {"format": "public-pilot-evaluation-v1", "key_id": "other-key",
                                     "payload": scores(payload)})
    with pytest.raises(Refused, match="not in the local trust store"):
        verify_evaluation(unknown, snapshot, trust, AT)
    scoped = {**trust, **trust_for(other, "other-key", "test-author", ["another-package"])}
    with pytest.raises(Refused, match="not trusted for this package"):
        verify_evaluation(unknown, snapshot, scoped, AT)
    foreign = {**trust, **trust_for(other, "other-key", "another-author", ["test-research"])}
    with pytest.raises(Refused, match="author mismatch"):
        verify_evaluation(unknown, snapshot, foreign, AT)
    tampered = signed(signer, scores(payload))
    tampered["payload"]["companies"]["DEMOA"]["composite"] = "99"
    with pytest.raises(Refused, match="signature"):
        verify_evaluation(tampered, snapshot, trust, AT)


def test_sign_evaluation_self_checks_against_the_snapshot(tmp_path, signer, snapshot, payload, monkeypatch, capsys):
    freeze(monkeypatch, AT)
    snapshot_file = write(tmp_path / "snapshot.json", snapshot)
    key_args = ["--key", signer[1], "--key-id", KEY_ID, "--snapshot", snapshot_file]
    code, output = call(capsys, ["sign-evaluation", write(tmp_path / "scores.json", scores(payload)),
                                 tmp_path / "evaluation.json"] + key_args)
    assert code == 0 and output["kind"] == "evaluation"
    bad = write(tmp_path / "bad.json", company(payload, "DEMOA", weight="0.5"))
    code, refusal = call(capsys, ["sign-evaluation", bad, tmp_path / "bad.signed.json"] + key_args)
    assert code == 2 and "differs from the payload target" in refusal["reason"]
    assert not (tmp_path / "bad.signed.json").exists()
    other, _ = new_key(tmp_path / "keys", "other.key")
    foreign = write(tmp_path / "foreign.json", authoring.sign_snapshot(other, KEY_ID, payload, AT))
    code, refusal = call(capsys, ["sign-evaluation", tmp_path / "scores.json", tmp_path / "x.json", "--key",
                                  signer[1], "--key-id", KEY_ID, "--snapshot", foreign])
    assert code == 2 and "signature" in refusal["reason"]


def test_render_evaluation_prints_an_inert_markdown_table(tmp_path, signer, payload, monkeypatch, capsys):
    evaluation = scores(payload)
    evaluation["method"]["description"] = "# Not a heading\n\nSecond <b>paragraph</b> with [a link](https://x.invalid)."
    evaluation["companies"]["DEMOB"]["note"] = "Pipe | and *stars* and `code`"
    code = cli.main(["render-evaluation", write(tmp_path / "evaluation.json", signed(signer, evaluation))])
    report = capsys.readouterr().out
    assert code == 0 and report == render(signed(signer, evaluation))
    lines = report.splitlines()
    assert "| Rank | Symbol | p1 | p2 | Composite | Decision | Weight |" in lines
    assert lines.index("| 1 | DEMOA | 80 | 65 | 72.5 | `include` | 0.4 |") < \
        lines.index("| 2 | DEMOB | 60 | 62 | 61 | `include` | 0.40 |")
    assert "\\# Not a heading" in lines and "<b>" not in report
    assert "Second \\<b\\>paragraph\\</b\\> with \\[a link\\](https://x.invalid)." in lines
    assert "- **DEMOB**: Pipe \\| and \\*stars\\* and \\`code\\`" in lines
    assert "not independently reviewed" in report


def test_render_drops_control_and_format_characters(signer, payload):
    evaluation = scores(payload)
    evaluation["companies"]["DEMOB"]["note"] = "Reset\x1bc bell\x07 csi\x9b2J bidi‮desrever zero​width"
    report = render(signed(signer, evaluation))
    assert not any(c in report for c in "\x1b\x07\x9b‮​")
    assert "- **DEMOB**: Resetc bell csi2J bididesrever zerowidth" in report.splitlines()


def test_text_that_is_not_valid_unicode_is_refused_not_crashing(tmp_path, signer, payload, capsys):
    evaluation = scores(payload)
    evaluation["companies"]["DEMOB"]["note"] = "lone \ud800 surrogate"
    # A lone surrogate cannot even be signed; render-evaluation checks structure only, so no signature is needed.
    document = {"format": "public-pilot-evaluation-v1", "key_id": KEY_ID, "payload": evaluation,
                "signature": "A" * 86 + "=="}
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(document, ensure_ascii=True))
    code, refusal = call(capsys, ["render-evaluation", path])
    assert code == 2 and "not valid Unicode text" in refusal["reason"]


def test_out_of_range_as_of_is_refused_not_crashing(tmp_path, signer, payload, capsys):
    path = write(tmp_path / "evaluation.json", signed(signer, scores(payload, as_of="0001-01-01T00:00:00+05:00")))
    code, refusal = call(capsys, ["render-evaluation", path])
    assert code == 2 and refusal["reason"] == "Date or time out of range"
