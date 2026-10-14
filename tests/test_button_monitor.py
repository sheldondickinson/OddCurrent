import pytest
from scripts.button_monitor import button_snapshot


def document():
    return {'info': {'oddcurrent': {'button_diagnostics_version': 1,
        'button_inputs': [{'gpio': p, 'level': 1, 'allocated': True} for p in (13, 14, 15, 16)],
        'device_credential': 'must-never-be-returned'}}}


def test_observed_low_is_pressed_and_only_fixed_input_fields_are_returned():
    d = document()
    d['info']['oddcurrent']['button_inputs'][3]['level'] = 0
    rows = button_snapshot(d)
    assert rows[-1] == {'gpio': 16, 'level': 0, 'pressed': True, 'allocated': True}
    assert all(set(row) == {'gpio', 'level', 'pressed', 'allocated'} for row in rows)


def test_allocation_failure_is_visible():
    d = document()
    d['info']['oddcurrent']['button_inputs'][0]['allocated'] = False
    assert button_snapshot(d)[0]['allocated'] is False


@pytest.mark.parametrize('change', ['old', 'duplicate', 'wrong_pin', 'bad_level', 'missing_allocation'])
def test_rejects_old_or_ambiguous_diagnostics(change):
    d = document()
    oc = d['info']['oddcurrent']
    if change == 'old':
        del oc['button_diagnostics_version']
    elif change == 'duplicate':
        oc['button_inputs'][0]['gpio'] = 14
    elif change == 'wrong_pin':
        oc['button_inputs'][0]['gpio'] = 35
    elif change == 'bad_level':
        oc['button_inputs'][0]['level'] = 2
    else:
        del oc['button_inputs'][0]['allocated']
    with pytest.raises(ValueError):
        button_snapshot(d)
