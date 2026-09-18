from typing import Dict, Iterable

import numpy as np

from nrgise.common.helper import convert_power_to_energy
from nrgise.economics.behind_the_meter.electricity_bill_calculator.data_classes import GridCharges, GridTariff
from nrgise.economics.behind_the_meter.electricity_bill_calculator.helper import raise_if_load_profile_is_not_one_year


def calculate_grid_charges(grid_tariff: GridTariff,
                           time_delta_seconds: int,
                           list_of_grid_power_utilization: Iterable[float]) -> GridCharges:
    """
    Calculates the grid charges based on the so-called usage hours ("Benutzungssstunden").
    """
    usage_hours = calculate_usage_hours(list_of_grid_power_utilization, time_delta_seconds)

    if usage_hours < 2500:
        power_price = grid_tariff.power_price_annual_period_of_use_below_2500
        energy_price = grid_tariff.energy_price_annual_period_of_use_below_2500
    else:
        power_price = grid_tariff.power_price_annual_period_of_use_above_2500
        energy_price = grid_tariff.energy_price_annual_period_of_use_above_2500

    power_cost = calculate_grid_power_cost_for_one_year(
        list_of_grid_power_utilization=list_of_grid_power_utilization,
        power_price=power_price,
    )

    energy_consumed_from_grid = convert_power_to_energy(list_of_grid_power_utilization, # type: ignore
                                                        time_delta_seconds)
    energy_cost = calculate_grid_energy_cost(get_energy_taken_from_grid_sum(energy_consumed_from_grid),
                                             energy_price)

    return GridCharges(power_cost=int(power_cost), energy_cost=int(energy_cost))


def calculate_grid_power_cost_for_one_year(list_of_grid_power_utilization: Iterable[float],
                                              power_price: float,
                                              ) -> float:
    """
    Calculates the part of the grid charges caused by the power utilization of the grid. Note that the price is
    calculated on a yearly basis. Please see https://www.energie-lexikon.info/registrierende_leistungsmessung.html
    for more information on how the power prices are determined.
    """
    list_of_grid_power_utilization = np.array(list_of_grid_power_utilization)
    # ToDo:
    # The completely correct way to determine the max_power like it is done in practice would be to:
    # 1. Convert from power to energy
    # 2. Resample energy to 15 min intervals
    # 3. Calculate power from 15 min intervals
    # See https://www.energie-lexikon.info/registrierende_leistungsmessung.html for more details
    max_power: float = max(list_of_grid_power_utilization)
    if max_power <= 0:
        return 0

    # Return yearly power cost
    return max_power * power_price


def calculate_usage_hours(list_of_grid_power_utilization: Iterable[float],
                          time_delta_seconds: int) -> float:
    """
    The calculation of the grid charges ("Netzentgelte") depends on the so-called usage hours ("Benutzungsstunden" or
    "Jahresbenutzungsdauer"). Note that the usage hours are calculated per year.
    The benutzungsstunden are calculated by:
    "benutzungsstunden" = "sum of energy of one year in kWh" / "max power of this year in kW"
    """
    list_of_grid_power_utilization = np.array(list_of_grid_power_utilization)
    max_power = max(list_of_grid_power_utilization)
    energy_utilization = convert_power_to_energy(list_of_grid_power_utilization, time_delta_seconds)
    # Filter out energy which was fed into the grid. We are only considering consumed energy.
    energy_taken_from_grid = energy_utilization[energy_utilization > 0]
    usage_hours: float = sum(energy_taken_from_grid) / (1 if max_power == 0 else max_power)
    return usage_hours


def get_energy_taken_from_grid_sum(list_of_grid_energy_utilization: Iterable[float]) -> float:
    list_of_grid_energy_utilization = np.array(list_of_grid_energy_utilization)
    energy_taken_from_grid: float = list_of_grid_energy_utilization[list_of_grid_energy_utilization > 0].sum()
    return energy_taken_from_grid


def get_energy_fed_into_grid_sum(list_of_grid_energy_utilization: Iterable[float]) -> float:
    list_of_grid_energy_utilization = np.array(list_of_grid_energy_utilization)
    # Getting sum of energy which was fed into the grid (when energy utilization is negative).
    energy_fed_into_grid: float = -1 * list_of_grid_energy_utilization[list_of_grid_energy_utilization < 0].sum()
    return energy_fed_into_grid


def calculate_grid_energy_cost(sum_energy_taken_from_grid: float,
                               energy_price: float) -> float:
    return sum_energy_taken_from_grid * energy_price


def calculate_income_from_feeding_in_energy(sum_of_energy_fed_into_grid: float,
                                            feed_in_tariff: float) -> float:
    return sum_of_energy_fed_into_grid * feed_in_tariff


def calculate_electricity_bill(grid_tariff: GridTariff,
                               list_of_grid_power_utilization: Iterable[float],
                               energy_price: float = 0.0697,
                               feed_in_tariff: float = 0.0608,
                               taxes: float = 0.0149,
                               time_delta_seconds: int = 900,
                               ) -> Dict:
    """
    Performs the calculation of the yearly electricity bill.

    Args:
        taxes: See https://www.bdew.de/service/daten-und-grafiken/bdew-strompreisanalyse/
        grid_tariff: A `GridTariff` which defines the costs of using the
            electricity grid. See `grid_tariffs.py` for different tariffs.
        list_of_grid_power_utilization: The power profile in kW that defines how the grid was used.
        energy_price: Price per kWh energy. The default value is set by using
            the arithmetic mean of the 1st half of 2024 of the day ahead stock
            market prices (https://energy-charts.info/).
        feed_in_tariff: Defines how many € is paid per kwh energy fed into the
            grid. The default value is based on the EEG 2024 and holds for PV
            systems between 100 and 1000 kWp. For more information see:
            https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/ErneuerbareEnergien/EEG_Foerderung/start.html
        time_delta_seconds: Defines the delta in seconds between two power values in the `list_of_grid_power_utilization`.
    Returns:
        A `dict` representing the electricity bill.
    """
    # # Electricity Bill Calculator

    # This tool can be used to calculate electricity bills for industrial and commercial sectors in Germany. It takes into
    # grid charges to provide accurate and comprehensive billing information.

    # **Note that the resulting bill returned from the calculator is net ("Netto"). To get the gross ("Brutto") prices,
    # 19% VAT ("Mehrwertsteuer") must be added.**

    list_of_grid_power_utilization = np.array(list_of_grid_power_utilization)

    raise_if_load_profile_is_not_one_year(list_of_grid_power_utilization, time_delta_seconds)

    grid_charges = calculate_grid_charges(grid_tariff,
                                          time_delta_seconds=time_delta_seconds,
                                          list_of_grid_power_utilization=list_of_grid_power_utilization)
    list_of_grid_energy_utilization = convert_power_to_energy(list_of_grid_power_utilization, time_delta_seconds)
    sum_energy_taken_from_grid = get_energy_taken_from_grid_sum(list_of_grid_energy_utilization)
    sum_energy_fed_into_grid = get_energy_fed_into_grid_sum(list_of_grid_energy_utilization)

    electricity_cost = calculate_grid_energy_cost(sum_energy_taken_from_grid, energy_price)
    electricity_taxes = sum_energy_taken_from_grid * taxes
    income = calculate_income_from_feeding_in_energy(sum_energy_fed_into_grid, feed_in_tariff)

    total_amount = electricity_cost + grid_charges.power_cost + grid_charges.energy_cost + electricity_taxes - income

    return {
        'sum_energy_taken_from_grid': sum_energy_taken_from_grid,
        'sum_energy_fed_into_grid': sum_energy_fed_into_grid,
        'peak_load': max(list_of_grid_power_utilization),
        'energy_cost': electricity_cost,
        'grid_charges': {
            'power_cost': grid_charges.power_cost,
            'energy_cost': grid_charges.energy_cost,
        },
        'income': income,
        'taxes': electricity_taxes,
        'usage_hours': calculate_usage_hours(list_of_grid_power_utilization, time_delta_seconds),
        'total_amount': total_amount,
    }
