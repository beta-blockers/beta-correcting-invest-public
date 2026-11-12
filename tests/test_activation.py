from copy import deepcopy
from datetime import timedelta
import pytest
from conftest import AT, FakeBroker
from public_pilot.common import Refused, digest, iso
from public_pilot.execution import execute
from public_pilot.planning import Limits, build_plan


def activation(payload, **changes):
    return {'package_sha256': digest(payload), 'symbols': ['DEMOA'], 'sides': {'DEMOA': 'buy'},
            'valid_until': iso(AT + timedelta(seconds=60)), 'decision_sha256': 'a' * 64, **changes}


def test_activation_restricts_symbols_without_modifying_research(payload, snapshot):
    original = deepcopy(payload)
    plan = build_plan(payload, snapshot, Limits(), AT, activation=activation(payload))
    assert {o['symbol'] for o in plan['orders']} == {'DEMOA'}
    assert payload == original and plan['package_sha256'] == digest(original)
    assert plan['desired_positions']['DEMOB'] == 0


@pytest.mark.parametrize('changes', [
    {'package_sha256': 'b' * 64}, {'valid_until': iso(AT)},
    {'symbols': ['UNKNOWN']}, {'symbols': ['DEMOA', 'DEMOA']},
    {'sides': {'DEMOA': 'short'}}, {'decision_sha256': 'missing'},
])
def test_bad_activation_refused(payload, snapshot, changes):
    with pytest.raises(Refused):
        build_plan(payload, snapshot, Limits(), AT, activation=activation(payload, **changes))


def test_rounding_cannot_reverse_activated_direction(payload, snapshot):
    snapshot['positions'] = {'DEMOA': '4'}
    # Midpoint is below the $400 target, but whole-share conservative target is 3.
    plan = build_plan(payload, snapshot, Limits(), AT, activation=activation(payload))
    assert plan['orders'] == [] and plan['desired_positions']['DEMOA'] == 4


def test_expired_activation_blocks_submission(store, author, payload, snapshot):
    trust, sign = author
    store.install(sign(payload), trust, AT)
    plan = build_plan(payload, snapshot, Limits(), AT, activation=activation(payload))
    identity = store.save_plan(plan)
    broker = FakeBroker(snapshot)
    with pytest.raises(Refused, match='Activation expired'):
        execute(store, identity, broker, trust, clock=lambda: AT + timedelta(seconds=61))
    assert broker.posts == 0


def test_empty_activation_makes_no_orders(payload, snapshot):
    plan = build_plan(payload, snapshot, Limits(), AT,
                      activation=activation(payload, symbols=[], sides={}))
    assert plan['orders'] == []
