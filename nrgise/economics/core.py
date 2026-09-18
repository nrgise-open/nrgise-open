from typing import Iterable

import numpy as np

from nrgise.economics.parameters import (
    DEFAULT_DISCOUNT_RATE,
    DEFAULT_INVESTMENT_HORIZON,
    DEFAULT_MAINTENANCE_COST_FACTOR,
    DEFAULT_STORAGE_REPLACEMENT_COST_FACTOR,
)

"""
The cost model defined in this document as well as the parameters used are described in the following sources:
- https://betterbat.de/usecases/ci
- https://doi.org/10.1016/j.apenergy.2025.125353
"""


def calculate_fixed_maintenance_cost_for_one_year(initial_invest: float,
                                                  maintenance_cost_factor: float = DEFAULT_MAINTENANCE_COST_FACTOR,
                                                  ) -> float:
    """
    Calculates the fixed maintenance cost for one year. Note that the variable maintenance costs are omitted here. If
    a storage is being cycled more than once a day, variable maintenance costs should be additionally taken into
    account.

    Args:
        initial_invest: How many € does the storage hardware cost initially. Note that this does not include EPC costs.
        maintenance_cost_factor: Factor of the initial storage hardware invest which is considered yearly maintenance cost.
    Returns:
        Maintenance cost for one year in €.
    """
    return initial_invest * maintenance_cost_factor


def calculate_maintenance_costs(initial_invest: float,
                                maintenance_cost_factor: float = DEFAULT_MAINTENANCE_COST_FACTOR,
                                investment_horizon_years: int = DEFAULT_INVESTMENT_HORIZON) -> np.ndarray:
    """
    Calculates maintenance costs for each year in the investment horizon. See
    `calculate_fixed_maintenance_cost_for_one_year()`
    for a description of the parameters.

    Returns:
        Maintenance cost in € for each year in the investment horizon.
    """
    maintenance_cost_for_one_year = calculate_fixed_maintenance_cost_for_one_year(
        initial_invest=initial_invest,
        maintenance_cost_factor=maintenance_cost_factor)
    return np.array([maintenance_cost_for_one_year] * investment_horizon_years)


def calculate_cost_of_one_replacement(initial_invest: float,
                                      replacement_cost_factor: float = DEFAULT_STORAGE_REPLACEMENT_COST_FACTOR) -> float:
    return initial_invest * replacement_cost_factor


def calculate_storage_replacement_costs_calendric_only(
        initial_storage_hardware_invest: float,
        storage_lifetime_in_years: float,
        replacement_cost_factor: float = DEFAULT_STORAGE_REPLACEMENT_COST_FACTOR,
        investment_horizon: int = DEFAULT_INVESTMENT_HORIZON) -> np.ndarray:
    """
    Estimate storage replacement costs assuming calendar aging only.

    Replacements are scheduled solely based on the storage lifetime in years and
    do not account for cycling dependent degradation. For more realistic aging
    behavior, use an aging model and simulate over multiple years.

    This function is useful when the simulation covers only a single year but
    storage replacement costs should still be approximated over the investment horizon.

    Returns:
        Replacement costs in € for each year in the investment horizon. Replacement is taking place where cost != 0€.
    """
    # ToDo: Refactor logic :)
    years_of_replacements = []
    year = int(storage_lifetime_in_years)
    while year < investment_horizon:
        years_of_replacements.append(year)
        year = year + int(storage_lifetime_in_years)
    cost_of_one_replacement = calculate_cost_of_one_replacement(initial_storage_hardware_invest,
                                                                replacement_cost_factor)
    return np.array([cost_of_one_replacement if year in years_of_replacements else 0
                     for year in range(investment_horizon)])


def discount_yearly(yearly_values_to_discount: Iterable[float],
                    discount_rate: float = DEFAULT_DISCOUNT_RATE) -> np.ndarray:
    # using t+1 in calculation, because range() starts with 0.
    """
    Discount yearly values to their present value.

    Each value is discounted as if it occurs at the end of the corresponding
    year, starting with year 1.

    Args:
        yearly_values_to_discount: Sequence of yearly values to discount.
        discount_rate: Annual discount rate.

    Returns:
        Array of discounted yearly values.
    """
    return np.array([value / (1 + discount_rate) ** (t + 1) for t, value in
                     zip(range(len(yearly_values_to_discount)), yearly_values_to_discount)])  # type: ignore


def calculate_npv(initial_invest: float,
                  discounted_cash_flow_per_year: np.ndarray,
                  discounted_maintenance_cost_per_year: np.ndarray,
                  discounted_replacement_cost_per_year: np.ndarray,
                  discounted_residual_value: float = 0,
                  ) -> float:
    """
    Calculate the net present value (NPV) of an investment.

    NPV is computed as discounted cash inflows minus discounted costs,
    including the initial investment, maintenance, and replacement costs,
    plus any discounted residual value.

    Args:
        initial_invest: Initial investment cost.
        discounted_cash_flow_per_year: Discounted yearly cash inflows.
        discounted_maintenance_cost_per_year: Discounted yearly maintenance costs.
        discounted_replacement_cost_per_year: Discounted yearly replacement costs.
        discounted_residual_value: Discounted residual value at the end of the investment horizon.

    Returns:
        Net present value of the investment.
    """
    return float(
        sum(discounted_cash_flow_per_year)
        - sum(discounted_maintenance_cost_per_year)
        - sum(discounted_replacement_cost_per_year)
        - initial_invest
        + discounted_residual_value,
    )


def calculate_storage_discounted_residual_value(initial_storage_hardware_invest: float,
                                                soh_end_of_investment_horizon: float,
                                                investment_horizon: float,
                                                discount_rate: float = DEFAULT_DISCOUNT_RATE,
                                                ) -> float:
    """
    Calculates the monetary value of the storage after the end of the simulation. Or in other words: How much € is the
    storage worth after the end of the calculation period?

    Note that the estimation of the residual value of a storage is very uncertain. This calculation can be considered
    optimistic as it "just" reduces the value of the storage based on the soh and the discounting of money. Another
    common approach is to just assume a residual storage value of 0.
    """
    residual_value: float = initial_storage_hardware_invest * soh_end_of_investment_horizon

    return float(residual_value / (1 + discount_rate) ** investment_horizon)


def calculate_static_amortisation(initial_invest: float, annual_income: float) -> float:
    """
    This calculation is static meaning that it calculates the amortisation time without considering a discount rate.
    The annual_income needs to be positive to give meaningful values.
    """
    if annual_income <= 0:
        return 0
    return initial_invest / annual_income


def calculate_lcoe(annual_energy_produced: np.ndarray,
                   discount_rate: float,
                   system_invest: float,
                   discounted_maintenance_costs: float,
                   discounted_replacement_costs: float,
                   discounted_residual_value: float,
                   ) -> float:
    """
    Calculates the levelized cost of electricity of a system. It is done using this formula:
    https://www.ise.fraunhofer.de/en/publications/studies/cost-of-electricity.html

    Args:
        annual_energy_produced: Array containing sum of energy produced in kWh per year.
        discount_rate: Yearly discount rate used.
        system_invest: The invest for the whole system for which LCOE should be calculated.
        discounted_maintenance_costs: Sum of discounted maintenance costs for the whole system over the investment horizon.
        discounted_replacement_costs: Sum of discounted replacement costs for the whole system over the investment horizon.
        discounted_residual_value: Discounted residual value of the whole system at the end of the investment horizon.
    Returns:
        LCOE in €
    """
    discounted_energy_produced = discount_yearly(annual_energy_produced, discount_rate)
    return float(
        (system_invest + discounted_maintenance_costs + discounted_replacement_costs - discounted_residual_value) / \
        sum(discounted_energy_produced))


def calculate_lcos(annual_energy_discharged: np.ndarray,
                   annual_charging_cost: np.ndarray,
                   discount_rate: float,
                   storage_invest: float,
                   discounted_maintenance_costs: float,
                   discounted_replacement_costs: float,
                   discounted_residual_value: float,
                   ) -> float:
    """
    Calculates the levelized cost of storage. It is done using this formula:
    https://www.sciencedirect.com/science/article/pii/S254243511830583X#bib20

    It can be interpreted like: How much does discharging of one kWh cost in the storage setup at hand.

    Args:
        annual_energy_discharged: Array containing sum of energy discharged in kWh per year.
        annual_charging_cost: Array containing cost to charge the storage per year.
        discount_rate: Yearly discount rate used.
        storage_invest: The invest for the whole system for which LCOE should be calculated.
        discounted_maintenance_costs: Sum of discounted maintenance costs for the whole system over the investment horizon.
        discounted_replacement_costs: Sum of discounted replacement costs for the whole system over the investment horizon.
        discounted_residual_value: Discounted residual value of the whole system at the end of the investment horizon.
    Returns:
        LCOS in €
    """
    discounted_energy_discharged: float = sum(discount_yearly(annual_energy_discharged, discount_rate))
    discounted_charging_cost: float = sum(discount_yearly(annual_charging_cost, discount_rate))
    return (storage_invest + discounted_maintenance_costs + discounted_replacement_costs + discounted_charging_cost -
            discounted_residual_value) / discounted_energy_discharged
