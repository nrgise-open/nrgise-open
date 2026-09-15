from typing import Optional, Sequence

import pandas as pd

from nrgise import EnergySystem
from nrgise.common.state import State
from nrgise.components import Battery, ChargePoint, Grid, PowerProfile


def build_profile_data(
        load_profile: Sequence[float],
        pv_profile: Sequence[float],
        time_index: Optional[pd.DatetimeIndex] = None,
) -> pd.DataFrame:
    if len(load_profile) != len(pv_profile):
        raise ValueError('Load and PV profiles must have equal lengths.')
    if time_index is None:
        time_index = pd.date_range('2012-01-01', periods=len(load_profile), freq='h')
    if len(time_index) != len(load_profile):
        raise ValueError('The time index and power profiles must have equal lengths.')
    return pd.DataFrame({'demand_el': load_profile, 'pv': pv_profile}, index=time_index)


def build_dummy_data() -> pd.DataFrame:
    return build_profile_data(
        load_profile=[0, 0, 0, 0, 0],
        pv_profile=[0, 0, 0, 0, 0],
    )


def build_energy_system_with_battery(
        data: pd.DataFrame,
        initial_soc: float = 0,
        battery_label: str = 'battery',
        battery_capacity: float = 100,
        battery_power: float = 100,
) -> EnergySystem:
    energy_system = EnergySystem(time_index=pd.DatetimeIndex(data.index))
    battery = Battery(
        label=battery_label,
        nom_power=battery_power,
        capacity=battery_capacity,
        time_delta_seconds=energy_system.time_delta_seconds,
        initial_soc=initial_soc,
    )
    load = PowerProfile(label='load', power_profile=data['demand_el'])
    pv = PowerProfile(label='pv', power_profile=data['pv'])
    energy_system.add_components(battery, pv, Grid(label='grid'), load)
    return energy_system


def build_energy_system_with_multiple_empty_batteries(data: pd.DataFrame) -> EnergySystem:
    energy_system = EnergySystem(time_index=pd.DatetimeIndex(data.index))
    batteries = [
        Battery(
            label=label,
            nom_power=100,
            capacity=100,
            initial_soc=0,
            time_delta_seconds=energy_system.time_delta_seconds,
        )
        for label in ('battery', 'battery2', 'battery3', 'battery4')
    ]
    load = PowerProfile(label='load', power_profile=data['demand_el'])
    pv = PowerProfile(label='pv', power_profile=data['pv'])
    energy_system.add_components(*batteries, pv, Grid(label='grid'), load)
    return energy_system


def build_energy_system_without_controllables(data: pd.DataFrame) -> EnergySystem:
    energy_system = EnergySystem(time_index=pd.DatetimeIndex(data.index))
    load = PowerProfile(label='load', power_profile=data['demand_el'])
    pv = PowerProfile(label='pv', power_profile=data['pv'])
    energy_system.add_components(pv, Grid(label='grid'), load)
    return energy_system


def build_energy_system_with_charge_point(
        charge_event_data: pd.DataFrame,
        load_profile: Optional[Sequence[float]] = None,
        pv_profile: Optional[Sequence[float]] = None,
        storage_soc: float = 1,
) -> EnergySystem:
    profile_length = len(charge_event_data)
    if load_profile is None:
        load_profile = [-float(time_step) for time_step in range(profile_length)]
    if pv_profile is None:
        pv_profile = [float(time_step) for time_step in range(profile_length)]
    data = build_profile_data(load_profile, pv_profile)
    energy_system = build_energy_system_with_battery(data, initial_soc=storage_soc)
    charge_point = ChargePoint(
        label='cp',
        charge_event_data=charge_event_data,
        time_delta_seconds=energy_system.time_delta_seconds,
    )
    energy_system.add_components(charge_point)
    return energy_system


def build_test_state(
        uncontrolled_power_balance: float = 0,
        time_step: int = 0,
        components_states: Optional[dict] = None,
        uncontrolled_power_contribution_per_component: Optional[dict[str, float]] = None,
) -> State:
    return State(
        time_step=time_step,
        uncontrolled_power_balance=uncontrolled_power_balance,
        uncontrolled_power_contribution_per_component=uncontrolled_power_contribution_per_component or {},
        components_states=components_states or {},
        date_time=pd.Timestamp('2024-01-01'),
    )
