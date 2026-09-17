import sys

import matplotlib.pyplot as plt
import numpy as np
import pyomo.environ as pyo
from common import read_and_preprocess_data

from nrgise.controllers.time_of_use_mpc_controller import build_optimization_problem

DELTA_TIME_HOURS = 0.25
NUM_OF_SIMULATION_STEPS = 4 * 24 * 7


if __name__ == '__main__':
    load, price, _ = read_and_preprocess_data()
    load, price, time = (load[:NUM_OF_SIMULATION_STEPS] * -1, price[:NUM_OF_SIMULATION_STEPS], range(NUM_OF_SIMULATION_STEPS))

    solver = pyo.SolverFactory('ipopt')

    m = build_optimization_problem(load, price, soc=0, power=50, capacity=200, time_delta_hours=DELTA_TIME_HOURS)
    solver.solve(m, tee=True)
    t = [time[i] * DELTA_TIME_HOURS for i in time]

    # compare to baseline
    baseline_cost = sum(load[load > 0] * price[load > 0])
    load_including_battery = load + np.array([(pyo.value(m.power[i])) for i in time])
    cost = sum(load_including_battery[load_including_battery > 0] * price[load_including_battery > 0])
    print('baseline cost: ' + str(baseline_cost))
    print('cost: ' + str(cost))
    print('savings in %: ' + str(cost / baseline_cost))

    fig1 = plt.figure()
    ax = plt.subplot()
    Line1 = ax.step(time, [(load[i]) for i in time], where="post", label='Residual Load')
    Line2 = ax.step(time, price*1000, '--', where="post", label='Price')
    Line3 = ax.step(time, load_including_battery, where="post", label='Load including Battery')
    Line4 = ax.step(time, [(pyo.value(m.power[i])) * -1 for i in time], where="post", label='Battery Power')
    plt.ylabel('Power Flows (kW) & Price (EUR/MWh)')
    plt.xlabel('Time Step')
    plt.title("Time of Use Price and Power Flows")
    ax.legend()
    ax.grid()
    plt.show(block=not sys.stdin.isatty())
