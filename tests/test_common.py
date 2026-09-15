from typing import List

import numpy as np
import pandas as pd
import pytest

from nrgise.common.helper import duplicate_data, flatten_dict, get_time_delta_seconds
from nrgise.common.types import is_time_series
from nrgise.simulator.simulation import SimulationStepResult


def test_flatten_dict():
    dict_to_flatten = {
        'a': 1,
        'b': 2,
        'c': {
            'a': 1,
            'b': 2,
        },
        'd': {
            'a': {
                'a': 1,
            },
            'b': [1, 2, 3, 4],
        },
    }
    expected = {
        'a': 1,
        'b': 2,
        'c.a': 1,
        'c.b': 2,
        'd.a.a': 1,
        'd.b': [1, 2, 3, 4],
    }
    flat_dict = flatten_dict(dict_to_flatten, sep='.')
    assert flat_dict == expected


def test_flatten_keeps_type_of_list():
    simulation_step_result = SimulationStepResult(time_step=0, date_time=pd.Timestamp.now(), uncontrolled_power_balance=0,
                                                  uncontrolled_power_contribution_per_component={}, components_states={},
                                                  grid_builder_usage=0, power_applied=0, power_requested=0,
                                                  additional_control_info={'pv_forecast': [0, 1, 2, 3]})
    flat_simulation_step_results = flatten_dict(vars(simulation_step_result))
    assert isinstance(flat_simulation_step_results['additional_control_info.pv_forecast'], List)


@pytest.mark.parametrize("index, expected", [
    (pd.date_range("1/1/2013", periods=1, freq="15min"), 900),
    (pd.date_range("1/1/2013", periods=2, freq="15min"), 900),
    (pd.date_range("1/1/2013", periods=2, end="1/2/2013"), 3600 * 24),
])
def test_get_time_delta_seconds(index, expected):
    tds = get_time_delta_seconds(index)
    assert tds == expected


@pytest.mark.parametrize("to_be_duplicated, num_duplicates, expected", [
    ([1, 2, 3], 3, [1, 2, 3, 1, 2, 3, 1, 2, 3]),
    (np.array([1, 2, 3]), 3, np.array([1, 2, 3, 1, 2, 3, 1, 2, 3])),
    (pd.Series([1, 2, 3]), 3, pd.Series([1, 2, 3, 1, 2, 3, 1, 2, 3])),
    (pd.DataFrame({'a': [1, 2], 'b': [1, 2]}), 3, pd.DataFrame({'a': [1, 2, 1, 2, 1, 2], 'b': [1, 2, 1, 2, 1, 2]})),
    ([1, 2, 3], 1, [1, 2, 3]),
    ([1, 2, 3], 0, []),
])
def test_duplicate_list(to_be_duplicated, num_duplicates, expected):
    duplicated_data = duplicate_data(to_be_duplicated, num_duplicates)
    if isinstance(duplicated_data, (pd.DataFrame, pd.Series)):
        assert duplicated_data.equals(expected)
    else:
        assert np.all(duplicated_data == expected)

@pytest.mark.parametrize("data, expected", [
    (pd.DataFrame(data=[[0, 1], [1, 2]],
                  index=pd.date_range(start='2024-01-01 00:00:00', periods=2, freq='15min')),
     True),
    (pd.Series(data=[0, 1],
                  index=pd.date_range(start='2024-01-01 00:00:00', periods=2, freq='15min')),
     True),
    (pd.Series([1,2]), False),
    (np.array([1,2,3]), False),
])
def test_is_time_series(data, expected):
    assert is_time_series(data) == expected
