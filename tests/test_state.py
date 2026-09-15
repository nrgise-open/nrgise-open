import pandas as pd

from nrgise.common.state import build_state
from nrgise.components import PowerProfile
from tests.helpers import build_dummy_data, build_energy_system_with_multiple_empty_batteries


def test_get_power_levels():
    pv_system_1 = PowerProfile(label='pv_1', power_profile=[1, 1, 1])
    pv_system_2 = PowerProfile(label='pv_2', power_profile=[2, 2, 2])
    state = build_state([pv_system_1, pv_system_2], time_step=0)
    assert state.uncontrolled_power_contribution_per_component == {'pv_1': 1, 'pv_2': 2}
    assert state.uncontrolled_power_balance == 3


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
