from datetime import timedelta

import pytest

from conftest import AT
from public_pilot.common import Refused, decimal, iso
from public_pilot.planning import Limits, build_plan


def test_weights_become_bounded_whole_shares_with_cash_reserve(payload, snapshot):
    plan = build_plan(payload, snapshot, Limits(), AT)
    assert plan["desired_positions"] == {"DEMOA": 3, "DEMOB": 3}
    assert all(decimal(o["qty"]) * decimal(o["limit_price"]) <= 250 for o in plan["orders"])
    assert sum(decimal(o["qty"]) * decimal(o["limit_price"]) for o in plan["orders"]) < 800


@pytest.mark.parametrize("change", [
    {"positions": {"FOREIGN": "1"}}, {"positions": {"DEMOA": "-1"}},
    {"positions": {"DEMOA": "1.5"}}, {"market_open": False}, {"cash": "-1"},
    {"open_orders": [{"id": "outside-order"}]},
])
def test_unsupported_account_state_refused(payload, snapshot, change):
    snapshot.update(change)
    with pytest.raises(Refused):
        build_plan(payload, snapshot, Limits(), AT)


def test_stale_and_wide_quotes_refused(payload, snapshot):
    snapshot["quotes"]["DEMOA"]["at"] = iso(AT - timedelta(minutes=3))
    with pytest.raises(Refused, match="Stale"):
        build_plan(payload, snapshot, Limits(), AT)
    snapshot["quotes"]["DEMOA"].update(at=iso(AT), bid="90")
    with pytest.raises(Refused, match="spread"):
        build_plan(payload, snapshot, Limits(), AT)


def test_sells_precede_buys_and_exits_remain_in_explicit_universe(payload, snapshot):
    snapshot.update(cash="100", positions={"DEMOA": "9"})
    payload["targets"] = {"DEMOB": "0.4"}
    plan = build_plan(payload, snapshot, Limits(max_turnover_usd="1500"), AT)
    sides = [o["side"] for o in plan["orders"]]
    assert sides == sorted(sides, key=lambda s: s != "sell")
    assert sum(int(o["qty"]) for o in plan["orders"] if o["side"] == "sell") == 9


def test_customer_limits_cannot_be_overridden_by_package(payload, snapshot):
    with pytest.raises(Refused, match="concentration"):
        build_plan(payload, snapshot, Limits(max_position_weight="0.2"), AT)
    with pytest.raises(Refused, match="turnover"):
        build_plan(payload, snapshot, Limits(max_turnover_usd="100"), AT)
