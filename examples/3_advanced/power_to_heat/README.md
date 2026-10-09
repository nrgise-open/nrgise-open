<!-- Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol -->
# Power To Heat

This example simulates one day in hourly time steps. It creates an energy
system with an electricity bus and a heat bus, using a constant 24-element
electrical load profile, a variable 24-element heat load profile, and a
`PowerToHeat` component with a COP of 3.

`HeatDemandController` reads the uncontrolled heat-bus deficit from `State`
and requests the electrical input needed for the `PowerToHeat` component to
balance it. The electricity grid supplies both the independent electrical load
and the additional electricity consumed for heating.

Run the example from this directory:

```bash
python power_to_heat.py
```

The simulation writes `results/simulation_results.csv` and generates
`results/power_to_heat.png`. The plot contains the electrical load, electrical
power applied to the `PowerToHeat` component, heat load, grid usage, and
residual heat balance.

To regenerate the plot from existing results:

```bash
python plot_power_to_heat.py
```
