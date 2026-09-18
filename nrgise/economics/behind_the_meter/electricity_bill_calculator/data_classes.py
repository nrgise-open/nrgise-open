from dataclasses import dataclass


@dataclass
class GridCharges:
    """
    GridCharges represent the "Netzentgelte". The prices are in €/kW(h).
    """
    power_cost: int
    energy_cost: int


@dataclass
class GridTariff:
    """
    ToDo: `GridTariff` represents a XXX
    Prices are in € per kW(h).
    """
    power_price_annual_period_of_use_below_2500: float
    power_price_annual_period_of_use_above_2500: float
    energy_price_annual_period_of_use_below_2500: float
    energy_price_annual_period_of_use_above_2500: float
