# Conventions

- All units concerning "electricity" are in **kW** or **kWh**
- All units concerning money are in €
- We follow the principle that: Power that "goes into" the local simulated energy system has positive values. Power that is "taken from" it has negative values. Examples:
    - The load profile usually contains negative values
    - The solar generation profile contains usually positive values.
    - When charging a storage, we use negative values as (from the perspective of the energy system) the power "goes out".
    - Power flowing from a `GridBuilder` (e.g. a "normal" grid connection point `Grid`) into the energy system is positive, 
      power flowing in the other direction is negative.