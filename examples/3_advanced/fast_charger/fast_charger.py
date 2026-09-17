import os
from typing import Tuple

import pandas as pd
from charge_event_dict_to_profile import charge_event_dict_to_pandas_profile

import nrgise
from nrgise.components import Battery, ChargePoint, Grid
from nrgise.controllers import FastChargePointController


def build_energy_system(date_time_index: pd.DatetimeIndex, profile: pd.DataFrame):
    es = nrgise.EnergySystem(time_index=date_time_index)
    grid = Grid(label='Grid')
    charge_point1 = ChargePoint(
        label='charge_point1',
        ev_charge_power_limit=-50,
        charge_event_data=profile,
        time_delta_seconds=15 * 60,
    )
    battery = Battery(
        label='battery',
        nom_power=100,
        capacity=100,
        time_delta_seconds=15 * 60,
    )
    es.add_components(grid, charge_point1, battery)
    return es


def create_data() -> Tuple[pd.DatetimeIndex, pd.DataFrame]:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(dir_path, 'data_charge_events.csv')
    charge_event_df = pd.read_csv(csv_file_path, sep=';')
    charge_event_dict = charge_event_df.to_dict('list')
    number_of_time_steps = 7 * 24 * 4
    dti = pd.date_range(start='2021-01-01 00:00', periods=number_of_time_steps, freq='15min')
    profile = charge_event_dict_to_pandas_profile(charge_event_dict, dti)
    return dti, profile


if __name__ == '__main__':
    dti, profile = create_data()
    es = build_energy_system(dti, profile)
    controller = FastChargePointController(
        charge_point_label='charge_point1',
        stationary_storage_label='battery',
        fast_charge_soc_limit=0.2,
    )
    simulation = nrgise.Simulation(es, controller)
    results = simulation.run()

    # ## uncomment to save results
    # # Save the csv file in the same directory as the current py file.
    # dir_path = os.path.dirname(os.path.realpath(__file__)) #noqa:ERA001
    # if not os.path.exists(dir_path + "/results/"):
    #     os.makedirs(dir_path + "/results/") #noqa:ERA001
    # csv_file_path = os.path.join(dir_path, 'results/simulation_results.csv') #noqa:ERA001
    #
    # results.to_csv(csv_file_path) #noqa:ERA001
