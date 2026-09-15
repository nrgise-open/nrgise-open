import pandas as pd
import pytest

from nrgise.components import Battery, ChargePoint
from nrgise.components.charge_point import _enforce_charge_limits


def build_charge_event_data():
    return pd.DataFrame({'capacity': [None, 10, 10, None], 'soc_arrival': [None, 0.1, 0.1, None]})


def test_charge_point_created_without_ev_connected_initially():
    cp = ChargePoint(
        label='cp',
        ev_charge_power_limit=-10,
        charge_event_data=None,  # type: ignore
        time_delta_seconds=900,
    )
    assert cp._electric_vehicle_connected() is False


def test_charge_point_ev_stays_disconnected():
    cp = ChargePoint(
        label='cp', ev_charge_power_limit=-10, charge_event_data=build_charge_event_data(), time_delta_seconds=900,
    )
    assert cp._electric_vehicle_connected() is False
    cp.handle_time_step_update(time_step=0)
    assert cp._electric_vehicle_connected() is False


def test_charge_point_connects_ev():
    cp = ChargePoint(
        label='cp', ev_charge_power_limit=-10, charge_event_data=build_charge_event_data(), time_delta_seconds=900,
    )
    cp.handle_time_step_update(time_step=1)
    assert cp._electric_vehicle_connected() is True


def test_charge_point_disconnects_ev():
    cp = ChargePoint(
        label='cp', ev_charge_power_limit=-10, charge_event_data=build_charge_event_data(), time_delta_seconds=900,
    )
    # Connect ev
    cp.electric_vehicle = Battery(
        label='ev',
        capacity=10,
        nom_power=10,
        initial_soc=0,
        time_delta_seconds=900,
    )
    cp.handle_time_step_update(time_step=0)
    assert cp._electric_vehicle_connected() is False


def test_charge_point_ev_stays_connected():
    cp = ChargePoint(
        label='cp', ev_charge_power_limit=-10, charge_event_data=build_charge_event_data(), time_delta_seconds=900,
    )
    # Connect ev
    cp.electric_vehicle = Battery(
        label='ev',
        capacity=10,
        nom_power=10,
        initial_soc=0,
        time_delta_seconds=900,
    )
    assert cp._electric_vehicle_connected() is True
    cp.handle_time_step_update(time_step=1)
    assert cp._electric_vehicle_connected() is True


def test_set_power_is_0_when_ev_is_disconnected():
    cp = ChargePoint(
        label='cp',
        ev_charge_power_limit=-10,
        charge_event_data=None,  # type: ignore
        time_delta_seconds=900,
    )
    assert cp._electric_vehicle_connected() is False
    assert cp.set_power_contribution(-100) == 0


@pytest.mark.parametrize(
    "discharge_limit, charge_limit, ev_capacity, power_set, expected",
    [
        (10, 0, 100, 100, 10), # Discharging EV, when Limit is enforced to 10
        (100, 0, 100, 100, 50), # Discharging EV, but only half of power can be returned as SCO is 0.5
        (0, -100, 100, -100, -50), # Charging EV, but only half, because of SOC
        (0, -10, 100, -100, -10), # Charging EV, but only with -10 because of limit enforcement

    ],
)
def test_set_power_ev_connected(discharge_limit, charge_limit, ev_capacity, power_set, expected):
    cp = ChargePoint(
        label='cp',
        ev_charge_power_limit=charge_limit,
        ev_discharge_power_limit=discharge_limit,
        charge_event_data=build_charge_event_data(),
        time_delta_seconds=3600,
    )
    # Connect ev
    cp.electric_vehicle = Battery(
        label='ev',
        capacity=ev_capacity,
        nom_power=ev_capacity,
        initial_soc=0.5,
        time_delta_seconds=3600,
    )
    assert cp.set_power_contribution(power_set) == expected

@pytest.mark.parametrize(
    "power, max_discharge, max_charge, expected",
    [
        (-100, 100, -100, -100),
        (-100, 100, -50, -50),
        (100, 100, -100, 100),
        (100, 50, -100, 50),
        (100, 50, 0, 50),
        (0, 50, 0, 0),
        (0, 0, 0, 0),

    ],
)
def test_enforce_charge_limits(power, max_discharge, max_charge, expected):
    assert _enforce_charge_limits(power, max_discharge, max_charge) == expected
