import pytest

from nrgise.controllers import (
    PeakShavingController,
    SelfConsumptionController,
    SelfConsumptionPeakShavingSequentialController,
)
from nrgise.forecasters import DataProfileForecaster
from tests.helpers import build_test_state


def build_sequential_controller(load_data, generation_data, cut_off_power_value, forecast_length):
    load_forecaster = DataProfileForecaster(load_data)
    pv_forecaster = DataProfileForecaster(generation_data)
    return SelfConsumptionPeakShavingSequentialController(
        load_forecaster=load_forecaster,
        pv_generation_forecaster=pv_forecaster,
        peak_shaving_cut_off_power_value=cut_off_power_value,
        forecast_length=forecast_length,
        storage_label='battery',
    )


def test_muc_get_action_runs_without_exception():
    sequential_controller = build_sequential_controller(
        load_data=[0, 0, 0, -5],
        generation_data=[0, 0, 0, 0],
        cut_off_power_value=-3,
        forecast_length=4,
    )
    _, controller_state = sequential_controller.get_action(build_test_state())
    # Active Controller is Peak Shaving as there is a Peak in the Forecast
    assert controller_state['active_controller'] is PeakShavingController


@pytest.mark.parametrize(
    "load, generation, expected_action, expected_controller", [
        # cases for self-consumption
        ([-1, -1], [10, 10], -9, SelfConsumptionController),
        # cases for peak-shaving (should happen when load+generation>cutoff)
        ([-11, -11], [0, 0], 1, PeakShavingController),
    ],
)
def test_muc_action(load, generation, expected_action, expected_controller):
    load_forecaster = DataProfileForecaster(load)
    pv_forecaster = DataProfileForecaster(generation)
    controller = SelfConsumptionPeakShavingSequentialController(
        load_forecaster, pv_forecaster,
        peak_shaving_cut_off_power_value=-10,
        forecast_length=1,
        storage_label='battery',
    )
    state = build_test_state(uncontrolled_power_balance=generation[0] + load[0])
    action, controller_state = controller.get_action(state)
    assert action == {'battery': expected_action}
    assert controller_state['active_controller'] is expected_controller


def test_muc_will_switch_to_peak_shaving_shortly_before_and_during_peak():
    load_data = [0, 0, 0, -11, 0, 0]
    generation_data = [0, 1, 2, 0, 0, 0]
    controller = build_sequential_controller(
        load_data=load_data,
        generation_data=generation_data,
        cut_off_power_value=-10,
        forecast_length=1,
    )
    # During the first two simulation steps, the controller should run in SelfConsumption mode
    for time_step in [0, 1, 4]:
        state = build_test_state(
            time_step=time_step,
            uncontrolled_power_balance=load_data[time_step] + generation_data[time_step],
        )
        _, controller_state = controller.get_action(state)
        assert controller_state['active_controller'] is SelfConsumptionController
    for time_step in [2, 3]:
        state = build_test_state(
            time_step=time_step,
            uncontrolled_power_balance=load_data[time_step] + generation_data[time_step],
        )
        _, controller_state = controller.get_action(state)
        assert controller_state['active_controller'] is PeakShavingController


@pytest.mark.parametrize(
    "residual_generation_forecast, cut_off_value, expected", [
        ([], -3, False),  # empty forecast
        ([1, 2.1, 2, 2, 1], -3, False),  # floats
        ([1, 2, 2, 2, 1], -3, False),  # strong false
        ([1, 2, -3, 2, 1], -3, False),  # edge case
        ([-1, -2, -5, -2, -1], -3, True),  # strong true
    ],
)
def test_forecasted_power_exceeds_cutoff_value(residual_generation_forecast, cut_off_value, expected):
    actual = SelfConsumptionPeakShavingSequentialController._forecasted_power_exceeds_cutoff_value(
        residual_generation_forecast=residual_generation_forecast,
        cut_off_power_value=cut_off_value)
    assert expected == actual
