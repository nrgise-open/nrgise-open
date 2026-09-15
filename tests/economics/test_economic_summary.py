import json
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from nrgise.economics import get_economic_summary


def test_summary_throws_if_inputs_unequal_length():
    with pytest.raises(Exception) as exception_info:
        get_economic_summary(initial_invest=100,
                             cash_flow_per_year_new=np.array([0, 0]),
                             cash_flow_per_year_baseline=np.array([1, 1]),
                             maintenance_cost_per_year_new=np.array([0]),
                             maintenance_cost_per_year_baseline=np.array([0]))
    assert exception_info.errisinstance(ValueError)


def test_economic_summary_includes_input_parameters():
    summary = get_economic_summary(initial_invest=100,
                                   cash_flow_per_year_new=np.array([10, 10]),
                                   cash_flow_per_year_baseline=np.array([5, 5]),
                                   )
    assert (summary.parameters['cash_flow_per_year_new'] == np.array([10, 10])).all()
    assert (summary.parameters['cash_flow_per_year_baseline'] == np.array([5, 5])).all()


def test_economic_summary_calculates_income_correctly():
    summary = get_economic_summary(initial_invest=100,
                                   cash_flow_per_year_new=np.array([10, 10]),
                                   cash_flow_per_year_baseline=np.array([3, 3]),
                                   maintenance_cost_per_year_new=np.array([1, 1]),
                                   )
    assert (summary.income_per_year == np.array([6, 6])).all()


def test_smoke_economic_summary():
    get_economic_summary(initial_invest=100,
                         cash_flow_per_year_new=np.array([0, 0]))
    assert True


def test_to_json():
    summary = get_economic_summary(initial_invest=100,
                                   cash_flow_per_year_new=np.array([10, 10]),
                                   cash_flow_per_year_baseline=np.array([3, 3]),
                                   maintenance_cost_per_year_new=np.array([1, 1]),
                                   )
    with TemporaryDirectory() as temporary_directory:
        file_path = Path(temporary_directory) / 'economic_summary.json'
        summary.to_json(str(file_path))

        with file_path.open(encoding='utf-8') as file:
            data = json.load(file)

        assert data['parameters']['initial_invest'] == 100
        assert data['parameters']['cash_flow_per_year_new'] == [10, 10]
        assert data['cash_flow_per_year_differences'] == [7, 7]


def test_summary_shows_warning_if_only_one_year_passed():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        get_economic_summary(initial_invest=100, cash_flow_per_year_new=np.array([1]))
        assert len(w) == 1
