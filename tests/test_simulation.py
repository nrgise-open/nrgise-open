import time

import numpy as np
import pandas as pd
import pytest

from nrgise import EnergySystem, Simulation
from nrgise.common.constants import HOURS_PER_YEAR
from nrgise.components import Grid
from nrgise.controllers import (
    ControllerABC,
    FastChargePointController,
    PeakShavingController,
    SelfConsumptionController,
    SelfConsumptionPeakShavingSequentialController,
)
from nrgise.forecasters import DataProfileForecaster, ForecastReplayForecaster
from nrgise.simulator.simulation import SimulationStepResult
from tests.helpers import (
    build_dummy_data,
    build_energy_system_with_battery,
    build_energy_system_with_charge_point,
    build_energy_system_with_multiple_empty_batteries,
    build_energy_system_without_controllables,
    build_profile_data,
)


@pytest.mark.parametrize(
    ('load_profile', 'pv_profile', 'expected_power_applied', 'expected_grid_builder_usage'),
    [
        ([-10, -10, -10, 0, -10], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [10, 10, 10, 0, 10]),
        ([0, 0, 0, 0, 0], [0, 10, 10, 10, 0], [0, -10, -10, -10, 0], [0, 0, 0, 0, 0]),
        ([-10, -10, -10, -10, -10], [0, 0, 20, 30, 0], [0, 0, -10, -20, 10], [10, 10, 0, 0, 0]),
    ],
    ids=['only_load', 'only_pv', 'mixed_load_and_pv'],
)
def test_self_consumption(
    load_profile,
    pv_profile,
    expected_power_applied,
    expected_grid_builder_usage,
):
    data = build_profile_data(load_profile=load_profile, pv_profile=pv_profile)
    energy_system = build_energy_system_with_battery(data, initial_soc=0)
    controller = SelfConsumptionController(storage_label='battery')
    simulation = Simulation(energy_system, controller)
    results = simulation.run()

    np.testing.assert_equal(results['power_applied'].to_numpy(), expected_power_applied)
    np.testing.assert_equal(results['grid_builder_usage'].to_numpy(), expected_grid_builder_usage)


def test_simulation_without_controller():
    data = build_profile_data(
        load_profile=[-10, -10, -10, -10, -10],
        pv_profile=[0, 0, 20, 30, 0],
    )
    simulation = Simulation(build_energy_system_without_controllables(data))
    results = simulation.run()
    expected_index = data.index.rename('date_time')
    pd.testing.assert_series_equal(
        results['uncontrolled_power_balance'],
        pd.Series([-10.0, -10.0, 10.0, 20.0, -10.0], index=expected_index, name='uncontrolled_power_balance'),
        check_freq=False,
    )
    pd.testing.assert_series_equal(
        results['grid_builder_usage'],
        pd.Series([10.0, 10.0, -10.0, -20.0, 10.0], index=expected_index, name='grid_builder_usage'),
        check_freq=False,
    )
    assert (results['power_applied'] == 0).all()


def test_peak_shaving():
    data = build_profile_data(
            load_profile=[-10, -10, -10, 0, -10],
            pv_profile=[0, 0, 0, 0, 0],
        )
    es = build_energy_system_with_battery(data, initial_soc=1)
    controller = PeakShavingController(cut_off_power_value=-5, storage_label='battery')
    simulation = Simulation(es, controller)
    results = simulation.run()
    # Check if all peaks could be shaved.
    assert (results['grid_builder_usage'] <= 5).all()
    # Check if power applied to battery causes the balance to be exactly -5 when the load is higher than -5
    assert ((data['demand_el'] + results['power_applied'])[data['demand_el'] < -5] == -5).all()


class DummyControllerMultipleControllables(ControllerABC):
    def get_action(self, state):  # noqa ARG002
        return {'battery': 0, 'battery2': 0, 'battery3': 0, 'battery4': 0}, None


def test_multiple_controllables_runs_without_exception():
    energy_system = build_energy_system_with_multiple_empty_batteries(build_dummy_data())
    controller = DummyControllerMultipleControllables()
    simulation = Simulation(energy_system, controller)
    simulation.run()


def test_results_with_multiple_controllables_contains_info_for_all_controllables():
    energy_system = build_energy_system_with_multiple_empty_batteries(build_dummy_data())
    controller = DummyControllerMultipleControllables()
    simulation = Simulation(energy_system, controller)
    results = simulation.run()
    assert {'power_applied.battery', 'power_requested.battery',
            'power_applied.battery2', 'power_requested.battery2',
            'power_applied.battery3', 'power_requested.battery3',
            'power_applied.battery4', 'power_requested.battery4'}.issubset(results.columns)


def test_energy_system_with_charge_point_no_ev():
    charge_event_data = pd.DataFrame({'capacity': [np.nan, np.nan, np.nan, np.nan],
                                      'soc_arrival': [np.nan, np.nan, np.nan, np.nan]})
    es = build_energy_system_with_charge_point(charge_event_data,
                                               load_profile=[0, 0, 0, 0],
                                               pv_profile=[0, 0, 0, 0],
                                               storage_soc=0)
    controller = FastChargePointController(
        charge_point_label='cp',
        stationary_storage_label='battery',
        stationary_storage_charging_power=10,
    )
    simulation = Simulation(es, controller)
    results = simulation.run()
    # battery is charged with 10 kW at every of the 4 time steps
    assert sum(results['grid_builder_usage']) == 40


def test_energy_system_with_charge_point_ev_fast_charge():
    charge_event_data = pd.DataFrame({'capacity': [1000, 1000, 1000, 1000],
                                      'soc_arrival': [0, 0, 0, 0]})
    es = build_energy_system_with_charge_point(charge_event_data,
                                               load_profile=[0, 0, 0, 0],
                                               pv_profile=[0, 0, 0, 0])
    controller = FastChargePointController(
        charge_point_label='cp',
        stationary_storage_label='battery',
        stationary_storage_charging_power=10,
    )
    simulation = Simulation(es, controller)
    results = simulation.run()
    # In the first 2 time steps, the battery can deliver enough power to fast charge: No utilization of the grid
    assert results['grid_builder_usage'].iloc[0] == 0
    assert results['grid_builder_usage'].iloc[1] == 0
    # In the last 2 time steps, the battery is empty: The grid is utilized
    assert results['grid_builder_usage'].iloc[2] == 10
    assert results['grid_builder_usage'].iloc[3] == 10


def test_energy_system_with_charge_point_ev_full():
    charge_event_data = pd.DataFrame({'capacity': [100, 100],
                                      'soc_arrival': [0.9, 0.9]})
    es = build_energy_system_with_charge_point(charge_event_data,
                                               load_profile=[0, 0],
                                               pv_profile=[0, 0])
    controller = FastChargePointController(charge_point_label='cp',
                                           stationary_storage_label='battery',
                                           stationary_storage_charging_power=10)
    simulation = Simulation(es, controller)
    results = simulation.run()
    # The stationary storage is used for fast charging even though the battery of the electric vehicle is full. The
    # power is fed into the grid
    assert results['grid_builder_usage'].iloc[0] == -40
    assert results['grid_builder_usage'].iloc[1] == -50


def test_energy_system_performance():
    time_index = pd.date_range(start='2021-01-01 00:00', periods=HOURS_PER_YEAR, freq='1h')
    data = build_profile_data([-1] * HOURS_PER_YEAR, [1] * HOURS_PER_YEAR, time_index)
    es = build_energy_system_with_battery(data, battery_label='', battery_capacity=10, battery_power=10)
    controller = SelfConsumptionController(storage_label='')
    simulation = Simulation(es, controller)
    start_time = time.time()
    simulation.run()
    execution_time = time.time() - start_time
    print(execution_time)
    assert execution_time < 1.5


def test_energy_system_performance_with_forecaster():
    time_index = pd.date_range(start='2021-01-01 00:00', periods=HOURS_PER_YEAR, freq='1h')
    data = build_profile_data([-1] * HOURS_PER_YEAR, [1] * HOURS_PER_YEAR, time_index)
    es = build_energy_system_with_battery(data, battery_label='', battery_capacity=10, battery_power=10)

    load_forecaster = DataProfileForecaster(data['demand_el'].to_numpy())
    pv_forecaster = DataProfileForecaster(data['pv'].to_numpy())

    controller = SelfConsumptionPeakShavingSequentialController(
        load_forecaster=load_forecaster,
        pv_generation_forecaster=pv_forecaster,
        peak_shaving_cut_off_power_value=-1,
        forecast_length=10,
        storage_label='',
    )

    simulation = Simulation(es, controller)
    start_time = time.time()
    simulation.run()
    execution_time = time.time() - start_time
    print(execution_time)
    assert execution_time < 1.5


def test_energy_system_performance_with_forecast_data_profile():
    time_index = pd.date_range(start='2021-01-01 00:00', periods=HOURS_PER_YEAR, freq='1h')
    data = build_profile_data([-1] * HOURS_PER_YEAR, [1] * HOURS_PER_YEAR, time_index)
    es = build_energy_system_with_battery(data, battery_label='', battery_capacity=10, battery_power=10)

    forecast_data_profile = pd.DataFrame(np.zeros((len(data), 10)))
    forecast_data_profile.index = es.time_index  # type: ignore

    load_forecaster = ForecastReplayForecaster(forecast_data_profile)
    pv_forecaster = ForecastReplayForecaster(forecast_data_profile)

    controller = SelfConsumptionPeakShavingSequentialController(
        load_forecaster=load_forecaster,
        pv_generation_forecaster=pv_forecaster,
        peak_shaving_cut_off_power_value=-1,
        forecast_length=10,
        storage_label='',
    )

    simulation = Simulation(es, controller)
    start_time = time.time()
    simulation.run()
    execution_time = time.time() - start_time
    print(execution_time)
    assert execution_time < 1.5


def test_results_contains_same_date_times_as_input():
    date_time_index = pd.date_range(start='2021-01-01 00:00', periods=HOURS_PER_YEAR, freq='1h')
    grid = Grid(label='grid')
    es = EnergySystem(time_index=date_time_index)
    es.add_components(grid)
    simulation = Simulation(es)
    results = simulation.run()
    assert (results.index == date_time_index).all()

def test_simulation_results_preserve_additional_control_info():
    class ControllerWithListInfo(ControllerABC):
        def get_action(self, state):  # noqa: ARG002
            return {}, {'pv_forecast': [0, 1, 2]}

    date_time_index = pd.date_range(start='2021-01-01 00:00', periods=1, freq='1h')
    energy_system = EnergySystem(time_index=date_time_index)
    energy_system.add_components(Grid(label='grid'))
    results = Simulation(energy_system, ControllerWithListInfo()).run()

    assert results['additional_control_info.pv_forecast'].iloc[0] == [0, 1, 2]

def test_hooks():
    hook_calls = []
    def simulation_hook(_: Simulation, simulation_step_result: SimulationStepResult):
        hook_calls.append(simulation_step_result.time_step)

    time_index = pd.date_range(start='2021-01-01 00:00', periods=20, freq='1h')
    data = build_profile_data([-1] * 20, [1] * 20, time_index)
    es = build_energy_system_with_battery(data, battery_label='', battery_capacity=10, battery_power=10)
    controller = SelfConsumptionController(storage_label='')
    simulation = Simulation(es, controller)
    simulation.register_hook(simulation_hook)
    simulation.run()
    assert hook_calls[-1] == 19
