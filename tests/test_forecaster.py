
import numpy as np
import pandas as pd
import pytest

from nrgise.common.state import State
from nrgise.forecasters import DataProfileForecaster, ForecastReplayForecaster


def _state_with_time_step(time_step: int) -> State:
    return State(
        time_step=time_step,
        uncontrolled_power_balance=0,
        uncontrolled_power_contribution_per_component={},
        components_states={},
        date_time=pd.Timestamp.now(),
    )


def test_data_profile_forecaster_forecasts_sequential_load_correctly():
    load_data = np.array([0, 1, 2, 3, 4])
    load_forecaster = DataProfileForecaster(forecast_data=load_data, standard_deviation=0)
    load_forecaster.fit(state=_state_with_time_step(0))
    forecast = load_forecaster.predict(forecast_length=4)
    np.testing.assert_array_equal(forecast, load_data[1:])


def test_data_profile_forecaster_returns_current_value():
    load_data = np.array([0, 1, 2, 3, 4])
    load_forecaster = DataProfileForecaster(forecast_data=load_data, standard_deviation=10)
    load_forecaster.fit(state=_state_with_time_step(2))
    assert load_forecaster.get_current_value() == 2


@pytest.mark.parametrize("load_data, time_step, expected",
                         [
                             ([1, 2, 3, 4], 0, [2, 3, 4]),
                             ([1, 2, 3, 4], 1, [3, 4, 0]),
                             ([1, 2, 3, 4], 4, [0, 0, 0]),
                             ([1, 2, 3, 4], 5, [0, 0, 0]),
                         ],
                         )
def test_data_profile_forecaster_extends_with_0_if_forecast_data_not_available(load_data, time_step, expected):
    load_forecaster = DataProfileForecaster(forecast_data=load_data, standard_deviation=0)
    load_forecaster.fit(_state_with_time_step(time_step))
    forecast = load_forecaster.predict(forecast_length=3)
    np.testing.assert_array_equal(forecast, expected)


@pytest.mark.parametrize("pandas_type", [True, False])
def test_forecast_replay_forecaster_accepts_forecast_defined_as_matrix(pandas_type):
    date_time_index = pd.date_range(start='2024-01-01 00:00:00', periods=3, freq='15min')
    forecast_data = np.array([[0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 5]])

    forecasts = pd.DataFrame(data=forecast_data, index=date_time_index)  # type: ignore
    uut = ForecastReplayForecaster(forecast_data=forecasts) if pandas_type else \
        ForecastReplayForecaster(forecast_data=forecast_data)
    uut.fit(state=_state_with_time_step(0))
    prediction = uut.predict(forecast_length=2)
    np.testing.assert_array_equal(prediction, [0, 1])


def test_forecast_replay_forecaster_fit_then_predict():
    date_time_index = pd.date_range(start='2024-01-01 00:00:00', periods=3, freq='15min')
    forecast_data = [[0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 5]]

    forecasts = pd.DataFrame(data=forecast_data, index=date_time_index)  # type: ignore
    uut = ForecastReplayForecaster(forecast_data=forecasts)
    for i in range(2):
        uut.fit(state=_state_with_time_step(i))
        prediction = uut.predict(forecast_length=4)
        np.testing.assert_array_equal(prediction, forecasts.iloc[i].to_numpy())


def test_forecast_replay_forecaster_throws_if_forecast_length_longer_then_data():
    date_time_index = pd.date_range(start='2024-01-01 00:00:00', periods=3, freq='15min')
    forecast_data = [[0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 5]]

    forecasts = pd.DataFrame(data=forecast_data, index=date_time_index)
    uut = ForecastReplayForecaster(forecast_data=forecasts)
    uut.fit(state=_state_with_time_step(0))
    with pytest.raises(Exception) as exception_info:
        uut.predict(forecast_length=5)
    assert exception_info.errisinstance(ValueError)
