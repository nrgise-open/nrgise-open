import os

import pandas as pd
import plot_sc

from nrgise import EnergySystem, Simulation, economics
from nrgise.components import AgingLinearCapacityWrapper, Battery, Grid, Load, Pv
from nrgise.controllers import SelfConsumptionController

PV_PEAK_POWER = 400
BATTERY_CAPACITY = 800

def read_data(pv_peak_power=PV_PEAK_POWER) -> pd.DataFrame:
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data/load_and_pv.csv')

    data = pd.read_csv(
        csv_path,
        index_col=['time'],
        parse_dates=['time'],
    )
    data['generation'] = data['pv_generation_1_kwp'] * pv_peak_power
    return data


def create_energy_system(data: pd.DataFrame) -> EnergySystem:
    es = EnergySystem(time_index=data.index)  # type: ignore[arg-type]
    grid = Grid(label='grid')
    # Note that the load is defined by negative power values.
    load = Load(label='load', power_profile=data['load'])
    pv_system = Pv(label='pv', power_profile=data['generation'])
    battery = Battery(
        label='battery',
        time_delta_seconds=es.time_delta_seconds,
        nom_power=BATTERY_CAPACITY/4,
        capacity=BATTERY_CAPACITY,
    )
    aging_battery = AgingLinearCapacityWrapper(storage=battery, lifetime_in_years=10, max_cycles=5000, eol=0.7,
                                               replace_storage_when_eol_reached=True)
    es.add_components(grid, load, aging_battery, pv_system)
    return es


def simulate_self_consumption(es: EnergySystem) -> pd.DataFrame:
    controller = SelfConsumptionController(storage_label='battery')
    simulation = Simulation(energy_system=es, controller=controller)
    return simulation.run()


if __name__ == '__main__':
    data_load_pv = read_data()
    energy_system = create_energy_system(data_load_pv)

    results = simulate_self_consumption(energy_system)

    # show power flows in plot
    plot_sc.plot(results)

    # Use the NRGISE economics library to calculate economic cash flows and net present value

    # First we stretch the grid power utilization over the investment horizon of 10 years, as we
    # only simulated one year of operation.
    grid_power_utilization_investment_horizon = economics.stretch_data_over_investment_horizon(
        data=results['grid_builder_usage'], investment_horizon_years=10)

    # Second we calculate the cash flow based on a simplified electricity bill calculation. The cash flow here is negative, as it
    # corresponds to the cost of electricity.
    cash_flow = economics.calculate_cash_flow_per_year_based_on_simplified_electricity_bill(
        energy_price=0.20,
        power_price=100,
        feed_in_tariff=0.10,
        grid_power_use_over_investment_horizon=grid_power_utilization_investment_horizon,
    )

    # We need a baseline to compare our investment against.
    # We take the same "energy system", but without any pv or battery (meaning only the load).
    baseline_grid_power_utilization_investment_horizon = economics.stretch_data_over_investment_horizon(
        data=results['uncontrolled_power_contribution_per_component.load'] * (-1), investment_horizon_years=10)
    baseline_cash_flow = economics.calculate_cash_flow_per_year_based_on_simplified_electricity_bill(
        energy_price=0.20,
        power_price=100,
        feed_in_tariff=0.10,
        grid_power_use_over_investment_horizon=baseline_grid_power_utilization_investment_horizon,
    )

    initial_invest_pv = 500*PV_PEAK_POWER
    initial_invest_battery = 200*BATTERY_CAPACITY
    economic_summary = economics.get_economic_summary(initial_invest=initial_invest_pv+initial_invest_battery,
                                                      cash_flow_per_year_new=cash_flow,
                                                      cash_flow_per_year_baseline=baseline_cash_flow)

    print(economic_summary)


    ### uncomment to save results
    ## power flow results
    ## Save the csv file in the same directory as the current py file.
    # dir_path = os.path.dirname(os.path.realpath(__file__)) #noqa:ERA001
    # if not os.path.exists(dir_path + "/results/"):
    #     os.makedirs(dir_path + "/results/") #noqa:ERA001
    # csv_file_path = os.path.join(dir_path, 'results/simulation_results.csv') #noqa:ERA001
    # results.to_csv(csv_file_path) #noqa:ERA001

    ## economic results
    # economic_summary.to_json('results/economic-summary.json') #noqa ERA001
