"""News addon configuration: validate-news-config."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from public_pilot.common import Refused
from public_pilot.newsconfig import validate_news_config
from support import call, write

KIT = Path(__file__).resolve().parents[1] / "author-kit"
CONFIG = json.loads((KIT / "news-config.template.json").read_text())
PAYLOAD = json.loads((KIT / "payload.template.json").read_text())


def changed(change):
    config = deepcopy(CONFIG)
    change(config)
    return config


def test_template_is_valid_alone_and_against_the_template_payload(tmp_path, capsys):
    assert validate_news_config(CONFIG)["status"] == "valid"
    code, output = call(capsys, ["validate-news-config", KIT / "news-config.template.json",
                                 "--payload", KIT / "payload.template.json"])
    assert code == 0 and output == {"status": "valid", "product_id": "example-product",
                                    "package_id": "example-product", "symbols": 3, "sources": 2,
                                    "enabled_sources": 1, "edition_id": "example-product-2020-q2"}


@pytest.mark.parametrize("change, message", [
    (lambda c: c.update(thresholds={"buy": "0.5"}), "unknown document fields"),
    (lambda c: c.update(prompt="Score this news"), "unknown document fields"),
    (lambda c: c["sources"]["example-filings"].update(weight="2"), "unknown document fields"),
    (lambda c: c["symbols"]["DEMOA"].update(score_rule="x"), "unknown document fields"),
    (lambda c: c.pop("timezone"), "unknown document fields"),
    (lambda c: c.update(product_id="bad id"), "Invalid product_id"),
    (lambda c: c.update(monitor_from="2020/04/01"), "monitor_from must be a YYYY-MM-DD date"),
    (lambda c: c.update(epoch_end="2020-02-30"), "epoch_end must be a YYYY-MM-DD date"),
    (lambda c: c.update(monitor_from="2020-07-01"), "monitor_from must not be later than epoch_end"),
    (lambda c: c.update(timezone="New York"), "IANA time zone"),
    (lambda c: c.update(timezone="Mars/Olympus_Mons"), "Unknown time zone"),
    (lambda c: c.update(symbols={}), "symbols maps"),
    (lambda c: c["symbols"].update(demoa={"cik": None, "aliases": ["x"]}), "Invalid symbol"),
    (lambda c: c["symbols"]["DEMOA"].update(cik=-1), "cik"),
    (lambda c: c["symbols"]["DEMOA"].update(cik="320193"), "cik"),
    (lambda c: c["symbols"]["DEMOA"].update(cik=True), "cik"),
    (lambda c: c["symbols"]["DEMOA"].update(cik=12.0), "cik"),
    (lambda c: c["symbols"]["DEMOA"].update(aliases=[]), "aliases"),
    (lambda c: c["symbols"]["DEMOA"].update(aliases=[f"a{i}" for i in range(11)]), "aliases"),
    (lambda c: c["symbols"]["DEMOA"].update(aliases=["Same", "Same"]), "aliases"),
    (lambda c: c["symbols"]["DEMOA"].update(aliases=["x" * 101]), "aliases"),
    (lambda c: c.update(sources={}), "sources maps"),
    (lambda c: c["sources"].update({"Bad Name": {"enabled": True}}), "Source names"),
    (lambda c: c["sources"]["example-filings"].update(enabled="yes"), "enabled is true or false"),
])
def test_each_rule_is_enforced(change, message):
    with pytest.raises(Refused, match=message):
        validate_news_config(changed(change))


def test_ten_aliases_and_a_cik_are_accepted():
    config = changed(lambda c: c["symbols"]["DEMOA"].update(cik=1234567, aliases=[f"a{i}" for i in range(10)]))
    assert validate_news_config(config, PAYLOAD)["symbols"] == 3


@pytest.mark.parametrize("change, message", [
    (lambda c: c["symbols"].update(DEMOZ={"cik": None, "aliases": ["Demo Zeta"]}), "outside the payload universe: DEMOZ"),
    (lambda c: c.update(epoch_end="2020-07-01"), "epoch_end must not be later than valid_until"),
    (lambda c: c.update(package_id="other-product"), "names another package"),
])
def test_with_a_payload_symbols_package_and_epoch_must_fit_the_edition(change, message):
    with pytest.raises(Refused, match=message):
        validate_news_config(changed(change), PAYLOAD)


def test_epoch_end_is_compared_in_the_configured_time_zone():
    # valid_until is 2020-07-01T00:00Z: still June 30 in New York, already July 1 in Tokyo.
    with pytest.raises(Refused, match=r"2020-06-30 in America/New_York"):
        validate_news_config(changed(lambda c: c.update(epoch_end="2020-07-01")), PAYLOAD)
    tokyo = changed(lambda c: c.update(epoch_end="2020-07-01", timezone="Asia/Tokyo"))
    assert validate_news_config(tokyo, PAYLOAD)["status"] == "valid"
    with pytest.raises(Refused, match=r"2020-07-01 in Asia/Tokyo"):
        validate_news_config(changed(lambda c: c.update(epoch_end="2020-07-02", timezone="Asia/Tokyo")), PAYLOAD)


def test_an_invalid_payload_is_refused(tmp_path, capsys):
    broken = write(tmp_path / "payload.json", {**PAYLOAD, "targets": {"DEMOA": "0.9", "DEMOB": "0.9"}})
    code, refusal = call(capsys, ["validate-news-config", KIT / "news-config.template.json", "--payload", broken])
    assert code == 2 and "target weights" in refusal["reason"]
    code, refusal = call(capsys, ["validate-news-config", write(tmp_path / "list.json", [])])
    assert code == 2 and refusal["reason"] == "Expected an object"


def test_a_validity_end_near_the_last_representable_date_is_accepted():
    far = {**PAYLOAD, "valid_until": "9999-12-31T23:59:59+00:00"}
    config = changed(lambda c: c.update(timezone="Europe/Berlin", epoch_end="9999-12-31"))
    assert validate_news_config(config, far)["status"] == "valid"
