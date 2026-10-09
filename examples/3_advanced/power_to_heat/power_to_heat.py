# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from pathlib import Path

import pandas as pd
from heat_demand_controller import HeatDemandController
from plot_power_to_heat import plot_results

from nrgise import EnergySystem, Simulation
from nrgise.components import Grid, Load, PowerToHeat, Battery

HEAT_BUS = "heat"
COP = 3.0
POWER_TO_HEAT_LABEL = "power_to_heat"
THERMAL_STORAGE_LABEL = "thermal_storage"
THERMAL_STORAGE_CAPACITY = 24.0
THERMAL_STORAGE_POWER = 2.0
ELECTRIC_LOAD_PROFILE = [-4.0] * 24
HEAT_LOAD_PROFILE = [
    -6.0, -5.8, -5.5, -5.2, -5.0, -5.5,
    -7.0, -8.0, -7.0, -5.5, -4.0, -3.0,
    -2.5, -2.2, -2.5, -3.0, -4.5, -6.5,
    -8.0, -8.5, -8.0, -7.5, -7.0, -6.5,
]
EXAMPLE_DIRECTORY = Path(__file__).resolve().parent
RESULTS_PATH = EXAMPLE_DIRECTORY / "results" / "simulation_results.csv"
PLOT_PATH = EXAMPLE_DIRECTORY / "results" / "power_to_heat.png"


def create_energy_system() -> EnergySystem:
    time_index = pd.date_range(
        "2024-01-01",
        periods=len(ELECTRIC_LOAD_PROFILE),
        freq="1h",
    )
    energy_system = EnergySystem(time_index=time_index)

    grid = Grid(label="grid")
    electric_load = Load(
        label="electric_load",
        power_profile=ELECTRIC_LOAD_PROFILE,
    )
    heat_load = Load(
        label="heat_load",
        power_profile=HEAT_LOAD_PROFILE,
        power_bus=HEAT_BUS,
    )
    heater = PowerToHeat(
        label=POWER_TO_HEAT_LABEL,
        cop=COP,
        heat_bus=HEAT_BUS,
    )
    thermal_storage = Battery(
        label=THERMAL_STORAGE_LABEL,
        capacity=THERMAL_STORAGE_CAPACITY,
        nom_power=THERMAL_STORAGE_POWER,
        time_delta_seconds=energy_system.time_delta_seconds,
        power_bus=HEAT_BUS,
    )

    energy_system.add_components(grid, electric_load, heat_load, heater, thermal_storage)
    return energy_system


def run_example() -> pd.DataFrame:
    energy_system = create_energy_system()
    controller = HeatDemandController(
        power_to_heat_label=POWER_TO_HEAT_LABEL,
        thermal_storage_label=THERMAL_STORAGE_LABEL,
        thermal_storage_power=THERMAL_STORAGE_POWER,
        cop=COP,
        heat_bus=HEAT_BUS,
    )
    return Simulation(energy_system=energy_system, controller=controller).run()


def save_results(results: pd.DataFrame, output_path: Path = RESULTS_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path)


if __name__ == "__main__":
    results = run_example()
    save_results(results)
    plot_results(results_path=RESULTS_PATH, output_path=PLOT_PATH)
    print(f"Saved results to {RESULTS_PATH}")
    print(f"Saved plot to {PLOT_PATH}")
