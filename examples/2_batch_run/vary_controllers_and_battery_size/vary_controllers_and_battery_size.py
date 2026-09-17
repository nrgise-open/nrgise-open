import os
from dataclasses import asdict
from typing import Tuple

import numpy as np
import pandas as pd
import plot_ps_mcf

import nrgise
from nrgise import BatchRun, EnergySystem, Simulation
from nrgise.common.helper import get_time_delta_seconds
from nrgise.components import Battery, Grid, Load, Pv
from nrgise.controllers import (
    ControllerABC,
    PeakShavingController,
    SelfConsumptionController,
    SelfConsumptionPeakShavingSequentialController,
)
from nrgise.economics.tools import stretch_data_over_investment_horizon
from nrgise.forecasters import DataProfileForecaster

# Define Parameters which are the same for each simulation loop
ELECTRICITY_PRICE = 0.3  # per kWh
POWER_PRICE = 100
FEED_IN_TARIFF = 0.05
PRICE_PER_KWH_STORAGE_CAPACITY = 400
C_RATE = 1
INVESTMENT_HORIZON = 10
DISCOUNT_RATE = 0.06
PV_PEAK_INSTALLED = 400


class MyBatchRun(BatchRun):
    def __init__(
            self,
            result_directory_name,
            load_profile,
            pv_generation_profile,
            parameter_space,
            date_time_index,
            baseline_cash_flow: np.ndarray,
    ):
        self.load_profile = load_profile
        self.pv_generation_profile = pv_generation_profile
        self.date_time_index = date_time_index
        self.baseline_cash_flow = baseline_cash_flow
        super().__init__(parameter_space=parameter_space, result_directory_name=result_directory_name, max_workers=4)

    def _create_energy_system(self, parameters: dict) -> EnergySystem:
        load = Load(label='load', power_profile=self.load_profile)
        grid = Grid(
            label='grid')
        pv = Pv(label='pv', power_profile=self.pv_generation_profile)
        battery = Battery(
            label='battery',
            time_delta_seconds=get_time_delta_seconds(self.load_profile.index),
            capacity=parameters['capacity'],
            nom_power=parameters['capacity'] * C_RATE,
            initial_soc=1.0,
        )
        energy_system = EnergySystem(time_index=self.load_profile.index)
        energy_system.add_components(load, grid, pv, battery)
        return energy_system

    def _create_controller(self, parameters: dict) -> ControllerABC:
        controller_class = parameters['controller']['class']
        if controller_class is SelfConsumptionController:
            return SelfConsumptionController(storage_label='battery')

        cut_off = parameters['controller']['cut_off_power_value']
        if controller_class is PeakShavingController:
            return PeakShavingController(cut_off_power_value=cut_off, storage_label='battery')

        if controller_class is SelfConsumptionPeakShavingSequentialController:
            load_forecaster = DataProfileForecaster(np.array(self.load_profile), standard_deviation=0)
            pv_forecaster = DataProfileForecaster(np.array(self.pv_generation_profile), standard_deviation=0)

            return SelfConsumptionPeakShavingSequentialController(
                load_forecaster=load_forecaster,
                pv_generation_forecaster=pv_forecaster,
                peak_shaving_cut_off_power_value=cut_off,
                forecast_length=12,
                storage_label='battery',
            )
        raise ValueError("invalid controller")

    def perform_single_simulation(self, parameters: dict) -> Tuple[pd.DataFrame, dict]:  # SimulationResults, Summary
        energy_system = self._create_energy_system(parameters)
        # Create Controller with config of this iteration
        controller = self._create_controller(parameters)

        simulation = Simulation(controller=controller, energy_system=energy_system)
        single_run_trajectory = simulation.run()

        stretched_grid_powers = stretch_data_over_investment_horizon(single_run_trajectory['grid_builder_usage'],
                                                                     INVESTMENT_HORIZON)

        cash_flow = nrgise.economics.calculate_cash_flow_per_year_based_on_simplified_electricity_bill(
            energy_price=ELECTRICITY_PRICE, power_price=POWER_PRICE, feed_in_tariff=FEED_IN_TARIFF,
            grid_power_use_over_investment_horizon=stretched_grid_powers)

        storage_invest = parameters['capacity'] * PRICE_PER_KWH_STORAGE_CAPACITY

        economic_summary = nrgise.economics.get_economic_summary(initial_invest=storage_invest,
                                                                 cash_flow_per_year_new=cash_flow,
                                                                 cash_flow_per_year_baseline=self.baseline_cash_flow)
        summary = {
            # include simulation parameters, so they can be stored together with the simulation results :)
            'parameters': parameters,
            'economics': asdict(economic_summary),
            'baseline_cash_flow': self.baseline_cash_flow,
        }

        return single_run_trajectory, summary


def get_baseline_cash_flow(data: pd.DataFrame) -> np.ndarray:
    load = Load(label='load', power_profile=data['load'])
    grid = Grid(label='grid')
    pv = Pv(label='pv', power_profile=data['generation'])
    baseline_energy_system = EnergySystem(time_index=data.index)  # type: ignore[arg-type]
    baseline_energy_system.add_components(load, grid, pv)

    baseline_simulation = Simulation(energy_system=baseline_energy_system)
    baseline_results = baseline_simulation.run()

    stretched_grid_powers = stretch_data_over_investment_horizon(baseline_results['grid_builder_usage'],
                                                                 INVESTMENT_HORIZON)
    return nrgise.economics.calculate_cash_flow_per_year_based_on_simplified_electricity_bill(
        energy_price=ELECTRICITY_PRICE, power_price=POWER_PRICE, feed_in_tariff=FEED_IN_TARIFF,
        grid_power_use_over_investment_horizon=stretched_grid_powers)


def read_data() -> pd.DataFrame:
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data/load_and_pv.csv')
    data = pd.read_csv(
        csv_path,
        index_col=['time'],
        parse_dates=['time'],
    )
    data['generation'] = data['pv_generation_1_kwp'] * PV_PEAK_INSTALLED
    return data


if __name__ == '__main__':
    data = read_data()
    results_folder_path = os.path.join(os.path.dirname(__file__), 'results')
    # Calculate Baseline
    baseline_cash_flow = get_baseline_cash_flow(data)

    # Define parameter space which will be used
    # All possible parameter combinations will be used
    parameter_space = {
        'capacity': [0, 10, 20, 40, 60, 80, 100, 120, 140, 180],
        'controller': [
            # This is a shorthand expression which can be used if multiple controllers should be tested :-)
            # It will create one Dict per value defined in the array.
            *[{
                'class': SelfConsumptionPeakShavingSequentialController,
                'threshold': i,
                'cut_off_power_value': i * min(data['load'])} for i in [0.9, 0.925]
            ],
            {
                'class': SelfConsumptionController,
                'threshold': 1,
                'cut_off_power_value': min(data['load']),
            },
            *[{'class': PeakShavingController,
               'threshold': i,
               'cut_off_power_value': i * min(data['load'])} for i in [0.9, 0.925]
              ],
        ],
    }

    # run the simulation for all parameters
    batch_run = MyBatchRun(
        result_directory_name=results_folder_path,
        parameter_space=parameter_space,
        load_profile=data['load'],
        pv_generation_profile=data['generation'],
        date_time_index=data.index,
        baseline_cash_flow=baseline_cash_flow,
    )
    batch_run.run()

    # investigate results
    results = pd.read_csv(results_folder_path + '/batch_run_summary.csv', index_col=[0])
    plot_ps_mcf.generate_npv_vs_capacity_plot(results, results_folder_path)
