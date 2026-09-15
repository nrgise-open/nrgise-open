import numpy as np
import pandas as pd
import pytest

from nrgise import (
    EnergySystem,
    Simulation,
)
from nrgise.components import Battery, ChargePoint, Generator, Grid, Load, Pv
from nrgise.controllers import SelfConsumptionController
from tests.helpers import (
    build_dummy_data,
    build_energy_system_with_battery,
    build_energy_system_with_charge_point,
    build_energy_system_with_multiple_empty_batteries,
)


def test_controllable_components_setup():
    energy_system = build_energy_system_with_multiple_empty_batteries(build_dummy_data())
    energy_system.reset()
    assert energy_system.controllable_components['battery'] is energy_system.get_component_by_label('battery')
    assert energy_system.controllable_components['battery2'] is energy_system.get_component_by_label('battery2')
    assert energy_system.controllable_components['battery3'] is energy_system.get_component_by_label('battery3')
    assert energy_system.controllable_components['battery4'] is energy_system.get_component_by_label('battery4')


def test_perform_action_dispatches_actions_to_components():
    energy_system = build_energy_system_with_multiple_empty_batteries(build_dummy_data())
    energy_system.reset()
    controllable_components = energy_system.controllable_components
    energy_system.simulate_one_time_step({'battery': 0, 'battery2': -10, 'battery3': -50, 'battery4': -100})
    expected_soc = {'battery': 0, 'battery2': 0.1, 'battery3': 0.5, 'battery4': 1}
    for label, soc in expected_soc.items():
        battery = controllable_components[label]
        assert isinstance(battery, Battery)
        assert battery.soc == soc


@pytest.mark.parametrize(
    "action, energy_system_builder", [
        ({'battery': -10}, build_energy_system_with_battery),
        (
            {'battery': -10, 'battery2': -20, 'battery3': -30, 'battery4': -40},
            build_energy_system_with_multiple_empty_batteries,
        ),
    ],
)
def test_perform_action_returns_dict(action, energy_system_builder):
    energy_system = energy_system_builder(build_dummy_data())
    energy_system.reset()
    power_contribution_per_controllable, _, _ = energy_system.simulate_one_time_step(action)
    assert power_contribution_per_controllable == action


@pytest.mark.parametrize(
    "action", [{'battery': 0},
               {'battery': 0, 'battery2': 0},
               ],
)
def test_perform_action_controllable_length_missmatch_causes_exception(action):
    energy_system = build_energy_system_with_multiple_empty_batteries(build_dummy_data())
    energy_system.reset()
    with pytest.raises(Exception) as exception_info:
        energy_system.simulate_one_time_step(action)
    assert exception_info.errisinstance(ValueError)


@pytest.mark.parametrize(
    "action", [{'battery': 0, 'battery2': 0, 'battery3': 0, 'falsy_name': 0}],
)
def test_perform_action_controllable_name_missmatch_causes_key_error(action):
    energy_system = build_energy_system_with_multiple_empty_batteries(build_dummy_data())
    energy_system.reset()
    with pytest.raises(Exception) as exception_info:
        energy_system.simulate_one_time_step(action)
    assert exception_info.errisinstance(KeyError)


def test_controllable_components_length_does_not_change_when_multiple_reset():
    energy_system = build_energy_system_with_battery(build_dummy_data())
    energy_system.reset()
    num_of_controllable_components_after_one_reset = len(energy_system.controllable_components)
    energy_system.reset()
    energy_system.reset()
    num_of_controllable_components_after_multiple_resets = len(energy_system.controllable_components)
    assert num_of_controllable_components_after_one_reset == num_of_controllable_components_after_multiple_resets


def test_energy_system_with_no_grid_builder_fails():
    es = EnergySystem(pd.DatetimeIndex(build_dummy_data().index))
    with pytest.raises(Exception) as exception_info:
        es.get_grid_builder()
    assert exception_info.errisinstance(ValueError)


def test_energy_system_get_grid_builder():
    es = EnergySystem(pd.DatetimeIndex(build_dummy_data().index))
    generator = Generator(label='generator')
    es.add_components(generator)
    power_supply = es.get_grid_builder()
    assert power_supply.label == 'generator'


def test_simulate_one_time_step_returns_done_after_profile_is_done():
    energy_system = build_energy_system_with_battery(build_dummy_data())
    energy_system.reset()
    for _ in range(len(energy_system.time_index)):
        _, _, done = energy_system.simulate_one_time_step({'battery': 0})
    assert done is True


def test_simulate_one_time_step_returns_not_done_while_profile_not_done():
    energy_system = build_energy_system_with_battery(build_dummy_data())
    energy_system.reset()
    for _ in range(len(energy_system.time_index) - 1):
        _, _, done = energy_system.simulate_one_time_step({'battery': 0})
        assert done is False


def test_time_in_sync_between_components():
    charge_event_data = pd.DataFrame({'capacity': [np.nan, 10, np.nan, np.nan],
                                      'soc_arrival': [np.nan, 0.1, np.nan, np.nan]})
    es = build_energy_system_with_charge_point(charge_event_data)
    es.reset()
    _, next_state, _ = es.simulate_one_time_step({'battery': 0, 'cp': 0})
    assert next_state is not None
    assert next_state.uncontrolled_power_contribution_per_component['load'] == -1
    assert next_state.uncontrolled_power_contribution_per_component['pv'] == 1
    assert next_state.components_states['cp']['ev_connected'] is True


def test_time_in_sync_in_initial_state():
    charge_event_data = pd.DataFrame({'capacity': [10, np.nan, np.nan, np.nan],
                                      'soc_arrival': [0.1, np.nan, np.nan, np.nan]})
    es = build_energy_system_with_charge_point(charge_event_data)
    initial_state = es.reset()
    assert initial_state.uncontrolled_power_contribution_per_component['load'] == 0
    assert initial_state.uncontrolled_power_contribution_per_component['pv'] == 0
    assert initial_state.components_states['cp']['ev_connected'] is True


def test_adding_component_with_duplicated_label_throws():
    grid_1 = Grid(label='same_name')
    grid_2 = Grid(label='same_name')
    es = EnergySystem(pd.date_range("1/1/2012", periods=10, freq="h"))
    with pytest.raises(Exception) as exception_info:
        es.add_components(grid_1, grid_2)
    assert exception_info.errisinstance(ValueError)


def test_check_profile_data_length_raises_if_unequal_profiles():
    es = EnergySystem(pd.date_range("1/1/2012", periods=2, freq="h"))
    es.add_components(Load(label='load', power_profile=range(3)),
                      Pv(label='pv', power_profile=range(1)))
    with pytest.raises(Exception) as exception_info:
        es.reset()
    assert exception_info.errisinstance(ValueError)


def test_check_profile_data_length_passes_if_equal_profiles():
    es = EnergySystem(pd.date_range("1/1/2012", periods=3, freq="h"))
    es.add_components(Load(label='load', power_profile=range(3)),
    Pv(label='pv', power_profile=range(3)))
    es.reset()


def test_result_len_equals_profile_len():
    date_range = pd.date_range("1/1/2012", periods=3, freq="h")
    es = EnergySystem(date_range)
    es.add_components(Load(label='load', power_profile=range(3)),
                       Pv(label='pv', power_profile=range(3)),
                      Battery(label='',
                                                   nom_power=10,
                                                   capacity=10,
                                                   time_delta_seconds=3600),
                      Grid(label='grid'))
    simulation = Simulation(es, SelfConsumptionController(storage_label=''))
    results = simulation.run()
    assert len(results) == len(date_range)


@pytest.mark.parametrize("end_timestamp, simulation_length",
                         [(pd.Timestamp("1/2/2012 23:00:00"), 48),
                          (pd.Timestamp("1/2/2012 11:00:00"), 36)])
def test_stretch_time_in_es(end_timestamp, simulation_length):
    es = EnergySystem(pd.date_range("1/1/2012 0:00:00", periods=24, freq="h"))
    charge_point_event_data = pd.DataFrame({'capacity': range(24), 'soc_arrival': range(24)})
    cp = ChargePoint(label='cp',
                     ev_charge_power_limit=-100,
                     charge_event_data=charge_point_event_data,
                     time_delta_seconds=900)
    es.add_components(Load(label='load', power_profile=range(24)),
                       Pv(label='pv', power_profile=range(24)),
                      cp)
    es.stretch_time(end_timestamp)
    # Reset checks if all data profiles have same length as the time index
    es.reset()
    assert len(es.time_index) == simulation_length
    assert es.time_index[-1] == end_timestamp
