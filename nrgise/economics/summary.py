import json
import warnings
from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np

from nrgise.economics import (
    calculate_npv,
    calculate_static_amortisation,
    discount_yearly,
)
from nrgise.economics.parameters import DEFAULT_DISCOUNT_RATE, WARNING_FOR_UNSTRETCHED_SIMULATION_RESULTS


@dataclass
class EconomicSummary:
    """
    A summary of the economic analysis, created by `get_economic_summary()`.

    The summary describes the economics the system, optionally compared
    against a baseline system. Fields ending in `_differences` represent the
    difference between the new system and baseline case.
    """
    parameters: dict
    npv: float
    static_amortisation_time: float
    income_per_year: np.ndarray
    cash_flow_per_year_differences: np.ndarray
    maintenance_cost_per_year_differences: np.ndarray
    replacement_cost_per_year_differences: np.ndarray
    discounted_residual_value_difference: float

    def to_json(self, filename: str) -> None:
        """
        dumps the `EconomicSummary` to a JSON file.

        Args:
            filename: The path to the file.
        """
        def convert_ndarray(obj):  # type: ignore[no-untyped-def]
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, dict):
                return {k: convert_ndarray(v) for k, v in obj.items()}
            return obj

        data = asdict(self)
        serializable_data = convert_ndarray(data)
        with open(filename, 'w') as f:
            json.dump(serializable_data, f, indent=4)


def get_economic_summary(initial_invest: float,
                         cash_flow_per_year_new: np.ndarray,
                         cash_flow_per_year_baseline: Optional[np.ndarray] = None,
                         maintenance_cost_per_year_new: Optional[np.ndarray] = None,
                         maintenance_cost_per_year_baseline: Optional[np.ndarray] = None,
                         replacement_cost_per_year_new: Optional[np.ndarray] = None,
                         replacement_cost_per_year_baseline: Optional[np.ndarray] = None,
                         discounted_residual_value_new: float = 0.0,
                         discounted_residual_value_baseline: float = 0.0,
                         discount_rate: float = DEFAULT_DISCOUNT_RATE) -> EconomicSummary:
    """
    Creates a `EconomicSummary`. Note that it can be used get the summary for
    a new system or for a comparison against a baseline system.

    Args:
        initial_invest: Upfront investment cost of the new case.
        cash_flow_per_year_new: Per year cash flow of the new case, excluding
            maintenance, replacement, and residual value.
        cash_flow_per_year_baseline: Per year baseline cash flow. If None,
            zeros are assumed.
        maintenance_cost_per_year_new: Per year maintenance cost of the new
            case. If None, zeros are assumed.
        maintenance_cost_per_year_baseline: Per year baseline maintenance cost.
            If None, zeros are assumed.
        replacement_cost_per_year_new: Per year replacement cost of the new
            case. If None, zeros are assumed.
        replacement_cost_per_year_baseline: Per year baseline replacement cost.
            If None, zeros are assumed.
        discounted_residual_value_new: Discounted residual value of the new
            case at the end of the horizon.
        discounted_residual_value_baseline: Discounted residual value of the
            baseline case at the end of the horizon.
        discount_rate: Yearly discount rate used.

    Returns:
        `EconomicSummary`.
    """
    # Saves all parameters which have been defined locally so far (Meaning all function inputs)
    function_input_parameters = locals()

    # Setting default Values and converting to np.array()
    default_values = np.zeros(len(cash_flow_per_year_new))
    cash_flow_per_year_baseline = default_values if cash_flow_per_year_baseline is None else np.array(cash_flow_per_year_baseline)
    maintenance_cost_per_year_new = default_values if maintenance_cost_per_year_new is None else np.array(maintenance_cost_per_year_new)  # noqa
    maintenance_cost_per_year_baseline = default_values if maintenance_cost_per_year_baseline is None else np.array(maintenance_cost_per_year_baseline)  # noqa
    replacement_cost_per_year_new = default_values if replacement_cost_per_year_new is None else np.array(replacement_cost_per_year_new)  # noqa
    replacement_cost_per_year_baseline = default_values if replacement_cost_per_year_baseline is None else np.array(replacement_cost_per_year_baseline)  # noqa
    cash_flow_per_year_new = np.array(cash_flow_per_year_new)

    cash_flow_per_year_diff = cash_flow_per_year_new - cash_flow_per_year_baseline
    maintenance_cost_per_year_diff = maintenance_cost_per_year_new - maintenance_cost_per_year_baseline
    replacement_cost_per_year_diff = replacement_cost_per_year_new - replacement_cost_per_year_baseline
    discounted_residual_value_difference = discounted_residual_value_new - discounted_residual_value_baseline

    _error_check_economic_summary(cash_flow_per_year_diff, maintenance_cost_per_year_diff,
                                  replacement_cost_per_year_diff)

    npv = calculate_npv(
        initial_invest=initial_invest,
        discounted_cash_flow_per_year=discount_yearly(cash_flow_per_year_diff, discount_rate=discount_rate),
        discounted_maintenance_cost_per_year=discount_yearly(maintenance_cost_per_year_diff,
                                                             discount_rate=discount_rate),
        discounted_replacement_cost_per_year=discount_yearly(replacement_cost_per_year_diff,
                                                             discount_rate=discount_rate),
        discounted_residual_value=discounted_residual_value_difference)

    # Note that we simplify the calculation of the amortisation time as we assume that income_per_year will remain identical
    # over the investment horizon
    income_per_year = cash_flow_per_year_diff - replacement_cost_per_year_diff - maintenance_cost_per_year_diff
    static_amortisation_time = calculate_static_amortisation(initial_invest=initial_invest,
                                                             annual_income=income_per_year[0])
    # ToDo: Calculation of PI...
    return EconomicSummary(
        parameters=function_input_parameters,
        cash_flow_per_year_differences=cash_flow_per_year_diff,
        maintenance_cost_per_year_differences=maintenance_cost_per_year_diff,
        replacement_cost_per_year_differences=replacement_cost_per_year_diff,
        discounted_residual_value_difference=discounted_residual_value_difference,
        income_per_year=income_per_year,
        npv=npv,
        static_amortisation_time=static_amortisation_time,
    )


def _error_check_economic_summary(cash_flow_differences: np.ndarray,
                                  maintenance_cost_differences: np.ndarray,
                                  replacement_cost_differences: np.ndarray) -> None:
    if len(cash_flow_differences) != len(maintenance_cost_differences) or \
            len(maintenance_cost_differences) != len(replacement_cost_differences):
        raise ValueError('Passed arrays must have same length.')

    if len(cash_flow_differences) == 1:
        warnings.warn(WARNING_FOR_UNSTRETCHED_SIMULATION_RESULTS)
