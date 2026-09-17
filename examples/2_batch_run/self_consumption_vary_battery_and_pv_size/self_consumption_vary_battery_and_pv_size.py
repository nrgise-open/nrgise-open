import os
from dataclasses import asdict
from typing import Tuple

import numpy as np
import pandas as pd
import plot_ps_be

import nrgise
from nrgise import BatchRun, EnergySystem, Simulation
from nrgise.common import get_time_delta_seconds
from nrgise.components import Battery, Grid, Load, Pv
from nrgise.controllers import SelfConsumptionController
from nrgise.economics.tools import stretch_data_over_investment_horizon

# Define Parameters which are the same for each simulation loop
ELECTRICITY_PRICE = 0.25  # per kWh
POWER_PRICE = 100
FEED_IN_TARIFF = 0.062
PRICE_PER_PV_KWP = 1000
PRICE_PER_KWH_STORAGE_CAPACITY = 400
C_RATE = 1
INVESTMENT_HORIZON = 15
DISCOUNT_RATE = 0.079


class MyBatchRun(BatchRun):
    def __init__(
            self,
            result_directory_name: str,
            load_profile: pd.Series,
            pv_generation_profile: pd.Series,
            parameter_space,
            date_time_index,
            baseline_cash_flow: np.ndarray,
    ):
        self.load_profile = load_profile
        self.pv_generation_profile = pv_generation_profile
        self.date_time_index = date_time_index
        self.baseline_cash_flow = baseline_cash_flow
        super().__init__(parameter_space=parameter_space, result_directory_name=result_directory_name, max_workers=4)

    def _create_energy_system(self, parameters) -> EnergySystem:
        load = Load(label='load', power_profile=self.load_profile)
        grid = Grid(
            label='grid',
        )
        pv = Pv(
            label='pv',
            power_profile=self.pv_generation_profile * parameters['pv_peak_power'],
        )
        battery = Battery(
            label='battery',
            time_delta_seconds=int(get_time_delta_seconds(self.date_time_index)),
            capacity=parameters['capacity'],
            nom_power=parameters['capacity'] * C_RATE,
        )
        energy_system = EnergySystem(time_index=self.date_time_index)
        energy_system.add_components(load, grid, pv, battery)
        return energy_system

    def perform_single_simulation(self, parameters) -> Tuple[pd.DataFrame, dict]:  # SimulationResults, Summary
        energy_system = self._create_energy_system(parameters)

        controller = SelfConsumptionController(storage_label='battery')
        simulation = Simulation(controller=controller, energy_system=energy_system)
        single_run_trajectory = simulation.run()

        stretched_grid_powers = stretch_data_over_investment_horizon(single_run_trajectory['grid_builder_usage'],
                                                                     INVESTMENT_HORIZON)

        cash_flow = nrgise.economics.calculate_cash_flow_per_year_based_on_simplified_electricity_bill(
            energy_price=ELECTRICITY_PRICE, power_price=POWER_PRICE, feed_in_tariff=FEED_IN_TARIFF,
            grid_power_use_over_investment_horizon=stretched_grid_powers)

        storage_invest = parameters['capacity'] * PRICE_PER_KWH_STORAGE_CAPACITY
        pv_invest = parameters['pv_peak_power'] * PRICE_PER_PV_KWP

        economic_summary = nrgise.economics.get_economic_summary(initial_invest=storage_invest + pv_invest,
                                                                 cash_flow_per_year_new=cash_flow,
                                                                 cash_flow_per_year_baseline=self.baseline_cash_flow)
        summary = {
            # include simulation parameters, so they can be stored together with the simulation results :)
            'parameters': parameters,
            'economics': asdict(economic_summary),
            'baseline_cash_flow': self.baseline_cash_flow,
        }

        return single_run_trajectory, summary


def read_data() -> pd.DataFrame:
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data/load_and_pv.csv')
    return pd.read_csv(
        csv_path,
        index_col=['time'],
        parse_dates=['time'],
    )


def get_baseline_cash_flow(data: pd.DataFrame) -> np.ndarray:
    # Baseline System has only load and grid (no pv and no battery)
    load = Load(label='load', power_profile=data['load'])
    grid = Grid(label='grid')
    baseline_energy_system = EnergySystem(time_index=data.index)  # type: ignore[arg-type]
    baseline_energy_system.add_components(load, grid)

    baseline_simulation = Simulation(energy_system=baseline_energy_system)
    baseline_results = baseline_simulation.run()
    stretched_grid_powers = stretch_data_over_investment_horizon(baseline_results['grid_builder_usage'],
                                                                 INVESTMENT_HORIZON)
    return nrgise.economics.calculate_cash_flow_per_year_based_on_simplified_electricity_bill(
        energy_price=ELECTRICITY_PRICE, power_price=POWER_PRICE, feed_in_tariff=FEED_IN_TARIFF,
        grid_power_use_over_investment_horizon=stretched_grid_powers)


if __name__ == '__main__':
    data = read_data()
    results_folder_path = os.path.join(os.path.dirname(__file__), 'results')

    # Calculate baseline cash flow without a battery and PV system
    # the baseline cash flow is used to compare the economic performance of the different parameter combinations.
    baseline_cash_flow = get_baseline_cash_flow(data)

    # Define parameter space which will be used
    # All possible parameter combinations will be simulated
    parameter_space = {
        'capacity': [512, 1024, 2048, 4096],
        'pv_peak_power': [512, 1024, 2048, 4096],
    }

    # run the simulation for all parameters
    batch_run = MyBatchRun(
        result_directory_name=results_folder_path,
        parameter_space=parameter_space,
        load_profile=data['load'],
        pv_generation_profile=data['pv_generation_1_kwp'],
        date_time_index=data.index,
        baseline_cash_flow=baseline_cash_flow,
    )
    batch_run.run()

    # investigate result
    results = pd.read_csv(results_folder_path + '/batch_run_summary.csv')
    plot_ps_be.investigate_top_runs(results, results_dir_path=results_folder_path)
    plot_ps_be.investigate_optimal_run(results, results_dir_path=results_folder_path)
