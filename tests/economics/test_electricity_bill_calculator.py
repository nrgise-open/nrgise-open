import warnings

import numpy as np
import pytest

from nrgise.economics.behind_the_meter.electricity_bill_calculator.data_classes import GridCharges, GridTariff
from nrgise.economics.behind_the_meter.electricity_bill_calculator.helper import raise_if_load_profile_is_not_one_year
from nrgise.economics.behind_the_meter.electricity_bill_calculator.main import (
    calculate_grid_charges,
    calculate_grid_energy_cost,
    calculate_grid_power_cost_for_one_year,
    calculate_income_from_feeding_in_energy,
    calculate_usage_hours,
    get_energy_fed_into_grid_sum,
    get_energy_taken_from_grid_sum,
)


@pytest.mark.parametrize(
    "power_utilization, expected", [
        # 8760 * 60 * 60 is a timestep length of one year.
        ([10], 10),
        ([10, 100], 100),
        ([-10], 0),
    ],
)
def test_grid_power_cost_calculation(power_utilization, expected):
    power_cost = calculate_grid_power_cost_for_one_year(
        list_of_grid_power_utilization=power_utilization,
        power_price=1,
    )
    assert power_cost == expected


def test_calculate_usage_hours_division_by_zero():
    power_utilization = [0 for i in range(8760)]
    usage_hours = calculate_usage_hours(power_utilization, 60 * 60)
    assert usage_hours == 0


def test_calculate_usage_hours_equally_distributed_profile():
    power_utilization = [1 for i in range(8760)]
    usage_hours = calculate_usage_hours(power_utilization, 60 * 60)
    assert usage_hours == 8760


def test_calculate_usage_hours_one_peak():
    power_utilization = [1 for i in range(8759)]
    power_utilization.extend([2])
    usage_hours = calculate_usage_hours(power_utilization, 60 * 60)
    assert usage_hours == pytest.approx(4380.5, abs=1e-12)


def test_calculate_usage_hours_half_half():
    power_utilization = [1 for i in range(int(8760 / 2))]
    max_power = 2
    power_utilization.extend([max_power for i in range(int(8760 / 2))])
    usage_hours = calculate_usage_hours(power_utilization, 60 * 60)
    energy_used = sum(power_utilization)
    assert usage_hours == pytest.approx(energy_used / max_power, abs=1e-12)


def test_calculate_usage_hours_when_constantly_feeding_in():
    power_utilization = [-1 for i in range(8760)]
    usage_hours = calculate_usage_hours(power_utilization, 60 * 60)
    assert usage_hours == 0


@pytest.mark.parametrize(
    "power_utilization, time_delta_seconds, expected", [
        # 8760 * 60 * 60 is one year in seconds.
        # Cases where usage hours >= 2500
        (np.array([0]), 8760 * 60 * 60, GridCharges(power_cost=0, energy_cost=0)),
        (np.array([1]), 8760 * 60 * 60, GridCharges(power_cost=100, energy_cost=876000)),
        # Cases where usage hours < 2500
        (np.array([1, 1, 1, 1, 1, 1000]), 8760 * 60 * 10, GridCharges(power_cost=0, energy_cost=0)),
    ],
)
def test_calculate_grid_charges(power_utilization, time_delta_seconds, expected):
    grid_prices = GridTariff(power_price_annual_period_of_use_above_2500=100,
                             power_price_annual_period_of_use_below_2500=0,
                             energy_price_annual_period_of_use_above_2500=100,
                             energy_price_annual_period_of_use_below_2500=0)
    grid_charges = calculate_grid_charges(
        grid_tariff=grid_prices,
        time_delta_seconds=time_delta_seconds,
        list_of_grid_power_utilization=power_utilization)
    assert expected.power_cost == grid_charges.power_cost
    assert expected.energy_cost == grid_charges.energy_cost


def test_warning_raised_when_load_profile_unequal_one_year():
    with warnings.catch_warnings(record=True) as w:
        raise_if_load_profile_is_not_one_year(list_of_grid_power_utilization=np.array([0, 0, 0, 0, 0]),
                                              time_delta_seconds=900)
        assert len(w) == 1


def test_no_warning_raised_when_load_profile_almost_equal_one_year():
    raise_if_load_profile_is_not_one_year(list_of_grid_power_utilization=np.array([0 for _ in range(8700)]),
                                          time_delta_seconds=3600)


def test_get_energy_taken_from_grid_sum():
    energy_taken_from_grid = get_energy_taken_from_grid_sum([1, 0, -1, 1])
    assert energy_taken_from_grid == 2


def test_get_energy_fed_into_grid_sum():
    energy_fed_into_grid = get_energy_fed_into_grid_sum([1, 0, -1, 1])
    assert energy_fed_into_grid == 1


def test_calculate_income_from_feeding_in_energy():
    income_from_feeding_in = calculate_income_from_feeding_in_energy(1, 1)
    assert income_from_feeding_in == 1


def test_calculate_grid_energy_cost():
    income_from_feeding_in = calculate_grid_energy_cost(1, 1)
    assert income_from_feeding_in == 1
