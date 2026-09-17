import os

import pandas as pd

from nrgise import EnergySystem, Simulation
from nrgise.components import AgingLinearCapacityWrapper, Battery, Grid, PowerProfile
from nrgise.controllers import ProfileFollowerController


def get_dummy_load_data():
    date_time_index = pd.date_range(
        start="1/1/2012", end="31/12/2012", freq="h",
    )
    load_profile = pd.DataFrame({'load': [0 for i in range(len(date_time_index))]})
    load_profile.index = date_time_index
    return load_profile


def build_energy_system(data):
    es = EnergySystem(time_index=data.index)
    grid = Grid(label='grid')

    load = PowerProfile(label='load', power_profile=data['load'])
    battery = Battery(
        label='battery',
        time_delta_seconds=es.time_delta_seconds,
        nom_power=2000,
        capacity=10000,
        initial_soc=0.5,
    )
    aging_battery = AgingLinearCapacityWrapper(battery, 20, 10000, 0.7, True)
    es.add_components(grid, load, aging_battery)
    return es


def simulate_with_profile_follower_controller(es: EnergySystem) -> pd.DataFrame:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(dir_path, 'battery_action_profile.csv')
    battery_action_profile = pd.read_csv(csv_file_path, delimiter=';', index_col=0)
    # -1 because charge, discharge sign conversion
    control_profile = -1 * battery_action_profile['load']
    controller = ProfileFollowerController(control_profile, storage_label='battery')
    simulation = Simulation(energy_system=es, controller=controller)
    return simulation.run()


if __name__ == '__main__':
    # A dummy load profile is used to define the length of the simulation as well as the time delta between actions
    dummy_load_data = get_dummy_load_data()

    es = build_energy_system(dummy_load_data)
    results = simulate_with_profile_follower_controller(es)


    # ## uncomment to save results
    # # Save the csv file in the same directory as the current py file.
    # dir_path = os.path.dirname(os.path.realpath(__file__)) #noqa:ERA001
    # if not os.path.exists(dir_path + "/results/"):
    #     os.makedirs(dir_path + "/results/") #noqa:ERA001
    # csv_file_path = os.path.join(dir_path, 'results/simulation_results.csv') #noqa:ERA001
    #
    # results.to_csv(csv_file_path) #noqa:ERA001
