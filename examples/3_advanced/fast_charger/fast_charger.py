import os
from typing import Tuple

import pandas as pd

import nrgise
from nrgise.components import Battery, ChargeEvent, ChargePoint, ChargeSchedule, Grid
from nrgise.controllers import FastChargePointController


def build_energy_system(date_time_index: pd.DatetimeIndex, charge_schedule: ChargeSchedule):
    es = nrgise.EnergySystem(time_index=date_time_index)
    grid = Grid(label='Grid')
    charge_point1 = ChargePoint(
        label='charge_point1',
        ev_charge_power_limit=-50,
        charge_schedule=charge_schedule,
        time_index=date_time_index,
    )
    battery = Battery(
        label='battery',
        nom_power=100,
        capacity=100,
        time_delta_seconds=15 * 60,
    )
    es.add_components(grid, charge_point1, battery)
    return es


def create_data() -> Tuple[pd.DatetimeIndex, ChargeSchedule]:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(dir_path, 'data_charge_events.csv')
    charge_event_df = pd.read_csv(csv_file_path, sep=';')
    arrivals = pd.to_datetime(charge_event_df['time_stamp'], format='%d.%m.%Y %H:%M')
    departures = arrivals + pd.to_timedelta(charge_event_df['parking_time_minutes'], unit='min')
    charge_schedule = ChargeSchedule()
    for arrival, departure, capacity, soc_arrival in zip(
            arrivals, departures, charge_event_df['capacity'], charge_event_df['soc_arrival']):
        charge_schedule.add_charge_event(
            ChargeEvent(arrival=arrival, departure=departure, capacity=capacity, soc_arrival=soc_arrival))
    number_of_time_steps = 7 * 24 * 4
    dti = pd.date_range(start='2021-01-01 00:00', periods=number_of_time_steps, freq='15min')
    return dti, charge_schedule


if __name__ == '__main__':
    dti, charge_schedule = create_data()
    es = build_energy_system(dti, charge_schedule)
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
