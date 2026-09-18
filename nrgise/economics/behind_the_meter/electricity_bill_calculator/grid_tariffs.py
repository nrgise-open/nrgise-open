from nrgise.economics.behind_the_meter.electricity_bill_calculator.data_classes import GridTariff

NETZE_BW_2023_LOW_VOLTAGE = GridTariff(
                    power_price_annual_period_of_use_below_2500=19.83,
                    power_price_annual_period_of_use_above_2500=130.88,
                    energy_price_annual_period_of_use_below_2500=0.0643,
                    energy_price_annual_period_of_use_above_2500=0.0199,
)

NETZE_BW_2024_LOW_VOLTAGE = GridTariff(
                    power_price_annual_period_of_use_below_2500=23.14,
                    power_price_annual_period_of_use_above_2500=203.34,
                    energy_price_annual_period_of_use_below_2500=0.0888,
                    energy_price_annual_period_of_use_above_2500=0.0168,
)
