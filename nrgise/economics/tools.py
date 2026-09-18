import warnings

import numpy as np
import pandas as pd

from nrgise.common.helper import get_time_delta_seconds
from nrgise.common.types import is_time_series
from nrgise.economics.behind_the_meter.electricity_bill_calculator import GridTariff, calculate_electricity_bill
from nrgise.economics.parameters import WARNING_FOR_UNSTRETCHED_SIMULATION_RESULTS
from nrgise.tools import stretch_data_profile


def stretch_data_over_investment_horizon(data: pd.Series,
                                         investment_horizon_years: int) -> pd.Series:
    """
    Stretches a data profile by repeating over a given calculation period. This is necessary for the calculation of
    the economics for the hole `investment_horizon_years` if the simulation was performed for a shorter period of time (
    example: We simulated only one year of operation, but want to look into a investment horizon of 10 years).
    Note that the beginning is always set to the first date of the year, which is the start of the n-year calculation
    period.

    Args:
        data: The data profile to stretch. This must have a DateTimeIndex.
        investment_horizon_years: The number of years to stretch the data profile over.

    Returns:
        The stretched data profile as a time series with a DateTimeIndex.
    """
    assert isinstance(data.index, pd.DatetimeIndex), "`data.index` must be a DatetimeIndex"

    date_time_index = data.index
    end_time_step = date_time_index[0] + pd.DateOffset(years=investment_horizon_years) - pd.Timedelta(minutes=15)
    grid_power_utilization_calc_period, date_time_index_calc_period = stretch_data_profile(data,
                                                                                           date_time_index,
                                                                                           end_time_step)

    # Make stretched data profile start from the beginning of the year
    first_date = date_time_index_calc_period[0]
    new_start_date = pd.Timestamp(year=first_date.year, month=1, day=1)
    new_date_range = pd.date_range(start=new_start_date, periods=len(date_time_index_calc_period),
                                   freq=date_time_index_calc_period.freq)  # type: ignore

    return pd.Series(data=np.array(grid_power_utilization_calc_period), index=new_date_range)


def calculate_cash_flow_per_year_based_on_detailed_electricity_bill(grid_tariff: GridTariff,
                                                                    electricity_price: float,
                                                                    feed_in_tariff: float,
                                                                    taxes: float,
                                                                    grid_power_use_over_investment_horizon: pd.Series,
                                                                    ) -> np.ndarray:
    """
    Calculates the cash flow for each year based on the electricity bill
    calculator. For a description of the parameters, please see the
    `calculate_electricity_bill()` function.

    Returns:
        Cash flow for each year.
    """
    assert isinstance(grid_power_use_over_investment_horizon.index, pd.DatetimeIndex), \
        "`grid_power_use_over_investment_horizon.index` must be a DatetimeIndex"

    energy_bill_per_year = [calculate_electricity_bill(
        grid_tariff=grid_tariff,
        energy_price=electricity_price,
        feed_in_tariff=feed_in_tariff,
        taxes=taxes,
        list_of_grid_power_utilization=grid_power_utilization,
        time_delta_seconds=get_time_delta_seconds(grid_power_use_over_investment_horizon.index),
    ) for year, grid_power_utilization in grid_power_use_over_investment_horizon.groupby(pd.Grouper(freq='YE'))]

    if len(energy_bill_per_year) == 1:
        warnings.warn(WARNING_FOR_UNSTRETCHED_SIMULATION_RESULTS)

    return -1 * np.array([bill['total_amount'] for bill in energy_bill_per_year])


def calculate_cash_flow_per_year_based_on_simplified_electricity_bill(energy_price: float,
                                                                      power_price: float,
                                                                      feed_in_tariff: float,
                                                                      grid_power_use_over_investment_horizon: pd.Series,
                                                                      ) -> np.ndarray:
    """
    Simplified version of calculating electricity costs. Usage hours and taxes are ignored.

    Returns:
        Cash flow for each year.
    """
    if not is_time_series(grid_power_use_over_investment_horizon):
        raise ValueError("`grid_power_use_over_investment_horizon` must have DateTimeIndex")

    simplified_grid_tariff = GridTariff(power_price_annual_period_of_use_below_2500=power_price,
                                        power_price_annual_period_of_use_above_2500=power_price,
                                        energy_price_annual_period_of_use_below_2500=0,
                                        energy_price_annual_period_of_use_above_2500=0)

    return calculate_cash_flow_per_year_based_on_detailed_electricity_bill(
        grid_tariff=simplified_grid_tariff,
        electricity_price=energy_price,
        feed_in_tariff=feed_in_tariff,
        taxes=0,
        grid_power_use_over_investment_horizon=grid_power_use_over_investment_horizon)
