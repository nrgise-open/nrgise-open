# Data Profile Descriptions

## load_and_pv.csv

This quarter-hourly profile represents a C&I storage in a industrial
production site with a three-shift operation.
- The energy load per year is 1516MWh
- Max load is 242.3649kW
- The profile was generated using the [SynPRO toolbox](https://synpro-lastprofile.de/), which can create custom synthetic load and generation profiles for various use cases
- The size of the building is 30000 m^2 and its an one story building
- The pv generation profile represents a PV system with 1kWp installed. Bigger PV systems can be simulated
   by scaling the values.
- The pv generation profile was created using [PVGIS](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en)

This profile was created in the SynGHD project and later also used in other projects, like BetterBat.

## synthetic_day_ahead_prices_2019.csv

This file contains synthetically generated price data for 2019. It aims to model day ahead electricity prices for hourly prices in 2024.
The units are in MW and prices are in €/MWh.

Real price data can be downloaded from [energy-charts](https://www.energy-charts.info/) and used in a plug-and-play fashion.
