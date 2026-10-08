import pandas as pd

from nrgise.common.constants import ELECTRICITY_BUS
from nrgise.common.state import build_state
from nrgise.components import Load, PowerProfile
from nrgise.components.grid_builder.grid import Grid
from nrgise.components.pv.pv import Pv
from nrgise.energy_system import EnergySystem
from tests.helpers import build_dummy_data, build_energy_system_with_multiple_empty_batteries


def test_get_power_levels_electricity_only():
    es = EnergySystem(time_index=pd.DatetimeIndex(build_dummy_data()[0:3].index))
    es.add_components(Grid(label='grid'),
                       PowerProfile(label='pv_1', power_profile=[1, 1, 1]),
                       Pv(label='pv_2', power_profile=[2, 2, 2]))
    state = es.reset()

    assert state.uncontrolled_power_contribution_per_bus_and_component == {
        ELECTRICITY_BUS: {'pv_1': 1, 'pv_2': 2},
    }
    assert state.uncontrolled_power_balance_per_bus == {ELECTRICITY_BUS: 3}


def test_get_power_levels_mixed():
    # Load can be added by concrete Load component or by PowerProfile. Both should add up.
    es = EnergySystem(time_index=pd.DatetimeIndex(build_dummy_data()[0:3].index))
    es.add_components(Grid(label='grid'),
                       PowerProfile(label='load', power_profile=[-1, -1, -1]),
                       Load(label='load_2', power_profile=[-2, -1, -1]),
                       PowerProfile(label='heating', power_bus='heat_40c', power_profile=[-2, -2, -2]),
                       Load(label='heating_2', power_bus='heat_40c', power_profile=[-3, -2, -2]),
                       PowerProfile(label='heating_90c', power_bus='heat_90c', power_profile=[-20, -20, -20]),
                       Load(label='heating_90_c_2', power_bus='heat_90c', power_profile=[-30, -20, -20])
                       )
    state = es.reset()

    assert state.uncontrolled_power_contribution_per_bus_and_component == {
        ELECTRICITY_BUS: {'load': -1, 'load_2': -2},
        'heat_40c': {'heating': -2, 'heating_2': -3},
        'heat_90c': {'heating_90c': -20, 'heating_90_c_2': -30},
    }
    assert state.uncontrolled_power_balance_per_bus == {
        ELECTRICITY_BUS: -3,
        'heat_40c': -5,
        'heat_90c': -50,
    }


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

    assert state.uncontrolled_power_balance_per_bus == {'electricity': 0}
    assert state.components_states == {}
    assert state.uncontrolled_power_contribution_per_bus_and_component == {'electricity': {}}


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
