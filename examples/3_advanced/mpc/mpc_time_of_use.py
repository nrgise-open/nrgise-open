import pandas as pd
from common import plot_tou, read_and_preprocess_data

from nrgise import EnergySystem, Simulation
from nrgise.components import Battery, Grid, Load
from nrgise.controllers import TimeOfUseMPCController
from nrgise.forecasters import DataProfileForecaster

FORECAST_LENGTH = 24
NUM_OF_SIMULATION_STEPS = 24 * 4 * 2
STORAGE_CAPACITY = 200
STORAGE_POWER = 50


def create_energy_system() -> EnergySystem:
    es = EnergySystem(time_index=time_index)  # type: ignore[arg-type]
    grid = Grid(label='grid')
    load = Load(label='load', power_profile=load_profile)
    battery = Battery(
        label='battery',
        time_delta_seconds=es.time_delta_seconds,
        nom_power=STORAGE_POWER,
        initial_soc=0,
        capacity=STORAGE_CAPACITY,
    )
    es.add_components(grid, load, battery)
    return es


def simulate_with_tou_controller(es: EnergySystem) -> pd.DataFrame:
    controller = TimeOfUseMPCController(
        load_forecaster=load_forecaster,
        price_forecaster=price_forecaster,
        time_delta_seconds=es.time_delta_seconds,
        storage_label='battery',
        forecast_length=FORECAST_LENGTH,
        storage_model_power=STORAGE_POWER,
        storage_model_capacity=STORAGE_CAPACITY,
    )
    simulation = Simulation(energy_system=es, controller=controller)
    return simulation.run()


if __name__ == '__main__':
    load, price, time_index = read_and_preprocess_data()
    # create Forecaster
    load_forecaster = DataProfileForecaster(load, standard_deviation=0)
    price_forecaster = DataProfileForecaster(price, standard_deviation=0)
    load_profile, price_profile, time_index = (
        load[0: NUM_OF_SIMULATION_STEPS],
        price[0: NUM_OF_SIMULATION_STEPS],
        time_index[0: NUM_OF_SIMULATION_STEPS],
    )
    es = create_energy_system()
    results = simulate_with_tou_controller(es)

    fig1 = plot_tou(results, price_profile)

    # ## uncomment to save results
    # # Save the csv file in the same directory as the current py file.
    # dir_path = os.path.dirname(os.path.realpath(__file__)) #noqa:ERA001
    # if not os.path.exists(dir_path + "/results/"):
    #     os.makedirs(dir_path + "/results/") #noqa:ERA001
    # csv_file_path = os.path.join(dir_path, 'results/simulation_results.csv') #noqa:ERA001
    #
    # # print results to csv
    # results.to_csv(csv_file_path) #noqa:ERA001
    #
    # fig1.savefig(dir_path+"/results/" + "/mpc-time-of-use.jpg") #noqa:ERA001
