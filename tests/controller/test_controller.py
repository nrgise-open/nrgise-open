import numpy as np
import pytest

from nrgise.controllers import (
    FastChargePointController,
    PeakShavingController,
    ProfileFollowerController,
    SelfConsumptionController,
)
from tests.helpers import build_test_state


def test_self_consumption_controller_charge_when_generation():
    controller = SelfConsumptionController(storage_label='battery')
    state = build_test_state(uncontrolled_power_balance=10)
    action, _ = controller.get_action(state)
    # Remember: negative means charge the storage
    assert action == {'battery': -10}


def test_self_consumption_controller_discharge_when_demand():
    controller = SelfConsumptionController(storage_label='battery')
    state = build_test_state(uncontrolled_power_balance=-10)
    action, _ = controller.get_action(state)
    # Remember: positive means discharge the storage
    assert action == {'battery': 10}


def test_self_consumption_controller_noop_when_same():
    controller = SelfConsumptionController(storage_label='battery')
    state = build_test_state()
    action, _ = controller.get_action(state)
    assert action == {'battery': 0}


@pytest.mark.parametrize("residual_power_level, expected_storage_control_action",
                         [
                             (-150, 50),
                             (-50, -50),
                             (50, -150),
                         ],
                         )
def test_peak_shaving_controller_cuts_at_cut_off_power_value(residual_power_level, expected_storage_control_action):
    controller = PeakShavingController(cut_off_power_value=-100, storage_label='battery')
    state = build_test_state(uncontrolled_power_balance=residual_power_level)
    action, _ = controller.get_action(state)
    assert action == {'battery': expected_storage_control_action}


@pytest.mark.parametrize(
    "control_profile, number_timesteps, expected",
    [
        ((150, 0, 50), 3, [150, 0, 50]),
        ([150, 0, -50], 1, [150]),
        (np.array([150, 0, -50]), 5, [150, 0, -50, 150, 0]),
    ],
)
def test_profile_follower(control_profile, number_timesteps, expected):
    controller = ProfileFollowerController(control_profile, storage_label='battery')
    control_trajectory = [sum(controller.get_action()[0].values()) for i in range(number_timesteps)]
    assert control_trajectory == expected


def test_fast_charge_point_controller_charges_battery_when_no_ev_connected():
    state = build_test_state(
        components_states={'cp': {
            'ev_connected': False,
            'ev_soc': None,
            'ev_capacity': None,
        }},
    )
    cp_controller = FastChargePointController(
        charge_point_label='cp',
        stationary_storage_label='battery',
        stationary_storage_charging_power=10,
    )
    action, _ = cp_controller.get_action(state)
    assert action == {'cp': 0, 'battery': -10}


@pytest.mark.parametrize(
    "battery_soc, expected",
    [
        (0, {'cp': -10, 'battery': 0}),  # Case for slow charging if battery is empty
        (0.8, {'cp': -100, 'battery': 100}),  # Case for fast charging if battery almost full
    ],
)
def test_fast_charge_point_controller_charges_ev_when_ev_connected(battery_soc, expected):
    state = build_test_state(
        components_states={
            'cp': {
                'ev_connected': True,
                'ev_soc': 0,
                'ev_capacity': 100,
            },
            'battery': {
                'soh': 1,
                'capacity': 100,
                'equivalent_cycles': 0,
                'soc': battery_soc,
            }},
    )
    cp_controller = FastChargePointController(
        charge_point_label='cp',
        stationary_storage_label='battery',
        fast_charge_soc_limit=0.5,
        fast_charge_power=100,
        slow_charge_power=10,
        stationary_storage_charging_power=10)
    action, _ = cp_controller.get_action(state)
    assert action == expected
