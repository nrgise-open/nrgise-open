# MPC Time of Use
This example describes a time of use scenario:

A company with quarter-hourly load fluctuations installs a battery to take advantage of changes in hourly day-ahead prices.
This folder contains two different example scripts.

1. `optimal_control_problem_pyomo`, which runs a single instance of the optimal control problem using pyomo.
   In this case, it is assumed that the forecast for the price, load and generation data for the whole period is available.
2. `mpc_time_of_use`, which applies model predictive control. In each time step, the optimal control problem is solved in a closed loop manner.
In contrast to 1. only a forecast of a fixed length is given in each iteration.