import pandas as pd
import pytest

from nrgise.components import Battery, ChargePoint
from nrgise.components.charge_point import _enforce_charge_limits
from tests.helpers import build_charge_event, build_charge_schedule

TIME_INDEX = pd.date_range('2012-01-01', periods=4, freq='h')


def build_charge_point(charge_schedule=None, **kwargs):
    if charge_schedule is None:
        # EV connected at time steps 1 and 2
        charge_schedule = build_charge_schedule(build_charge_event(1, 3))
    return ChargePoint(
        label='cp',
        ev_charge_power_limit=kwargs.pop('ev_charge_power_limit', -10),
        charge_schedule=charge_schedule,
        time_index=TIME_INDEX,
        **kwargs,
    )


def test_charge_point_created_without_ev_connected_initially():
    cp = build_charge_point(build_charge_schedule())
    assert cp._electric_vehicle_connected() is False


def test_charge_point_ev_stays_disconnected():
    cp = build_charge_point()
    assert cp._electric_vehicle_connected() is False
    cp.handle_time_step_update(time_step=0)
    assert cp._electric_vehicle_connected() is False


def test_charge_point_connects_ev():
    cp = build_charge_point()
    cp.handle_time_step_update(time_step=1)
    assert cp._electric_vehicle_connected() is True


def test_charge_point_disconnects_ev():
    cp = build_charge_point()
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
    cp = build_charge_point()
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


def test_charge_point_disconnects_ev_at_departure():
    cp = build_charge_point()
    cp.handle_time_step_update(time_step=1)
    cp.handle_time_step_update(time_step=2)
    # Departure is at time step 3, which is exclusive
    cp.handle_time_step_update(time_step=3)
    assert cp.get_state() == {'ev_connected': False, 'ev_soc': None, 'ev_capacity': None}


def test_charge_point_distinguishes_consecutive_charge_events():
    charge_schedule = build_charge_schedule(
        build_charge_event(0, 2, capacity=10, soc_arrival=0.1),
        build_charge_event(2, 4, capacity=80, soc_arrival=0.5),
    )
    cp = build_charge_point(charge_schedule)
    cp.handle_time_step_update(time_step=0)
    first_electric_vehicle = cp.electric_vehicle
    cp.set_power_contribution(-5)
    cp.handle_time_step_update(time_step=1)
    assert cp.electric_vehicle is first_electric_vehicle
    cp.handle_time_step_update(time_step=2)
    assert cp.electric_vehicle is not first_electric_vehicle
    assert cp.get_state() == {'ev_connected': True, 'ev_soc': 0.5, 'ev_capacity': 80}


def test_charge_point_reset_disconnects_ev():
    cp = build_charge_point()
    cp.handle_time_step_update(time_step=1)
    cp.reset()
    assert cp._electric_vehicle_connected() is False
    # The same charge event is connected again after reset
    cp.handle_time_step_update(time_step=1)
    assert cp._electric_vehicle_connected() is True


def test_charge_point_data_profile_has_one_entry_per_time_step():
    charge_event = build_charge_event(1, 3)
    cp = build_charge_point(build_charge_schedule(charge_event))
    assert cp.data_profile == [None, charge_event, charge_event, None]


def test_set_power_is_0_when_ev_is_disconnected():
    cp = build_charge_point(build_charge_schedule())
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
    cp = build_charge_point(ev_charge_power_limit=charge_limit, ev_discharge_power_limit=discharge_limit)
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
