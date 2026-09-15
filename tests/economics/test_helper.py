import numpy as np
import pandas as pd
import pytest

from nrgise.economics import (
    calculate_cash_flow_per_year_based_on_simplified_electricity_bill,
    stretch_data_over_investment_horizon,
)


def test_stretch_data_over_calculation_period():
    date_time_index_february_only = pd.date_range(start='2020-02-01', end='2020-02-28', freq='h')
    data = [0 for _ in date_time_index_february_only]
    grid_power_util = pd.Series(index=date_time_index_february_only, data=data)
    stretched_ts = stretch_data_over_investment_horizon(grid_power_util, 15)
    stretched_ts_length = stretched_ts.index[-1] - stretched_ts.index[0]
    assert stretched_ts.index[0] == pd.Timestamp(year=2020, month=1, day=1)
    assert stretched_ts_length.days / 365 == pytest.approx(15, abs=0.01)


@pytest.mark.parametrize(
    "energy_price, power_price, feed_in_tariff, power, expected", [
        (1, 0, 0, 1, -8760), (0, 100, 0, 1, -100), (0, 0, 1, -1,  8760),
    ],
)
def test_calculate_cash_flow_based_on_simplified_electricity_bill(energy_price, power_price, feed_in_tariff, power,
                                                                  expected):
    date_time_index = pd.date_range(start='2021-01-01', end='2024-12-30 23:00:00', freq='h')
    data = [power for _ in date_time_index]
    grid_power_util = pd.Series(index=date_time_index, data=data)
    cash_flow = calculate_cash_flow_per_year_based_on_simplified_electricity_bill(
        energy_price=energy_price,
        power_price=power_price,
        feed_in_tariff=feed_in_tariff,
        grid_power_use_over_investment_horizon=grid_power_util)
    assert (cash_flow == np.array([expected] * 4)).all()
