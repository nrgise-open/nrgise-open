from nrgise.economics.behind_the_meter.electricity_bill_calculator.data_classes import GridTariff
from nrgise.economics.behind_the_meter.electricity_bill_calculator.main import calculate_electricity_bill
from nrgise.economics.core import (
    calculate_cost_of_one_replacement,
    calculate_fixed_maintenance_cost_for_one_year,
    calculate_lcoe,
    calculate_lcos,
    calculate_maintenance_costs,
    calculate_npv,
    calculate_static_amortisation,
    calculate_storage_discounted_residual_value,
    calculate_storage_replacement_costs_calendric_only,
    discount_yearly,
)
from nrgise.economics.summary import get_economic_summary
from nrgise.economics.tools import (
    calculate_cash_flow_per_year_based_on_detailed_electricity_bill,
    calculate_cash_flow_per_year_based_on_simplified_electricity_bill,
    stretch_data_over_investment_horizon,
)

__all__ = [
    "GridTariff",
    "calculate_cash_flow_per_year_based_on_detailed_electricity_bill",
    "calculate_cash_flow_per_year_based_on_simplified_electricity_bill",
    "calculate_cost_of_one_replacement",
    "calculate_electricity_bill",
    "calculate_fixed_maintenance_cost_for_one_year",
    "calculate_lcoe",
    "calculate_lcos",
    "calculate_maintenance_costs",
    "calculate_npv",
    "calculate_static_amortisation",
    "calculate_storage_discounted_residual_value",
    "calculate_storage_replacement_costs_calendric_only",
    "discount_yearly",
    "get_economic_summary",
    "stretch_data_over_investment_horizon",

]
