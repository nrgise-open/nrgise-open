import numpy as np
import pytest

import nrgise.economics as economics


def test_calculate_replacement_cost_per_year():
    replacement_cost_per_year = economics.calculate_storage_replacement_costs_calendric_only(
        initial_storage_hardware_invest=100,
        storage_lifetime_in_years=3,
        replacement_cost_factor=0.1,
        investment_horizon=5)
    assert (replacement_cost_per_year == [0, 0, 0, 10, 0]).all()


def test_calculate_maintenance_costs():
    maintenance_cost_per_year = economics.calculate_maintenance_costs(initial_invest=100,
                                                                      maintenance_cost_factor=0.1,
                                                                      investment_horizon_years=3)
    assert (maintenance_cost_per_year == [10, 10, 10]).all()


def test_discount_yearly():
    discounted_values = economics.discount_yearly([1, 1], 0.1)
    # Expected values where calculated manually
    assert discounted_values == pytest.approx([0.91, 0.83], abs=0.01)


def test_discounted_residual_value():
    discounted_residual_value = economics.calculate_storage_discounted_residual_value(
        initial_storage_hardware_invest=100,
        investment_horizon=10,
        soh_end_of_investment_horizon=0.5,
        discount_rate=0,
    )
    assert discounted_residual_value == 50


@pytest.mark.parametrize(
    "initial_invest, annual_income, expected", [
        (100, 10, 10),
    ],
)
def test_calculate_static_amortisation(initial_invest, annual_income, expected):
    static_amortisation_time = economics.calculate_static_amortisation(initial_invest, annual_income)
    assert static_amortisation_time == expected


def test_calculate_npv():
    # Compare function results with https://www.calculatestuff.com/financial/npv-calculator
    discounted_cash_flow = economics.discount_yearly([100, 100, 100, 100, 100], discount_rate=0.06)
    npv = economics.calculate_npv(
        initial_invest=1000,
        discounted_cash_flow_per_year=discounted_cash_flow,
        discounted_residual_value=0,
        discounted_maintenance_cost_per_year=np.array([0] * 5),
        discounted_replacement_cost_per_year=np.array([0] * 5),
    )
    assert npv == pytest.approx(-578.76, abs=0.01)


def test_lcoe():
    annual_energy_produced = np.array([100, 100, 100])
    lcoe = economics.calculate_lcoe(annual_energy_produced=annual_energy_produced,
                                    discount_rate=0, system_invest=100, discounted_residual_value=0,
                                    discounted_maintenance_costs=0, discounted_replacement_costs=0)
    assert lcoe == 100 / 300


def test_lcos():
    annual_energy_discharged = np.array([100, 100, 100])
    annual_charging_cost = np.array([100, 0, 0])
    lcoe = economics.calculate_lcos(annual_energy_discharged=annual_energy_discharged,
                                    annual_charging_cost=annual_charging_cost, discount_rate=0, storage_invest=100,
                                    discounted_residual_value=0, discounted_maintenance_costs=0,
                                    discounted_replacement_costs=0)
    assert lcoe == 200 / 300
