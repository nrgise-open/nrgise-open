import pandas as pd

from nrgise.common.state import build_state
from nrgise.components import PowerProfile
from nrgise.components.grid_builder.grid import Grid
from nrgise.energy_system import EnergySystem
from tests.helpers import build_dummy_data, build_empty_energy_system, build_energy_system_with_multiple_empty_batteries


def test_get_power_levels_electricity_only():
    es = EnergySystem(time_index=pd.DatetimeIndex(build_dummy_data()[0:3].index))
    es.add_components(Grid(label='grid'), 
                      PowerProfile(label='pv_1', power_profile=[1, 1, 1]), 
                      PowerProfile(label='pv_2', power_profile=[2, 2, 2]))
    state = es.reset()

    assert state.uncontrolled_electrical_power_contribution_per_component == {'pv_1': 1, 'pv_2': 2}
    assert state.uncontrolled_electrical_power_balance == 3
    assert state.uncontrolled_thermal_power_balance == 0
    assert state.uncontrolled_thermal_power_contribution_per_component == {}


def test_build_state_contains_components_states():
    energy_system = build_energy_system_with_multiple_empty_batteries(build_dummy_data())
    energy_system.reset()
    state = build_state(
        components=energy_system.components,
        time_step=0,
        include_components_state=True,
        date_time=pd.Timestamp.now(),
    )
    assert state.components_states['battery']['soc'] == 0 and \
           state.components_states['battery2']['soc'] == 0 and \
           state.components_states['battery3']['soc'] == 0 and \
           state.components_states['battery4']['soc'] == 0

def test_state_empty_energy_system():
    es = EnergySystem(time_index=pd.DatetimeIndex(build_dummy_data().index))
    es.add_components(Grid(label='grid'))
    state = es.reset()

    assert state.uncontrolled_electrical_power_balance == 0 
    assert state.uncontrolled_thermal_power_balance == 0
    assert state.components_states == {}
    assert state.uncontrolled_electrical_power_contribution_per_component == {}
    assert state.uncontrolled_thermal_power_contribution_per_component == {}

def test_state_attr_getter():
    # Testing functionality of state to access its elements using the [] indexer.
    energy_system = build_energy_system_with_multiple_empty_batteries(build_dummy_data())
    energy_system.reset()
    state = build_state(
        components=energy_system.components,
        time_step=0,
    )
    assert state['time_step'] == 0


def test_date_time_is_set():
    state = build_state([], time_step=0)
    assert isinstance(state.date_time, pd.Timestamp)
