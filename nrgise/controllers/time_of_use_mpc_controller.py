from typing import Any, Dict, Tuple

import numpy as np
import pyomo.environ as pyo  # type: ignore

from nrgise.common.state import State
from nrgise.common.types import GenericSequence
from nrgise.controllers.controller_abc import ControllerABC
from nrgise.forecasters.forecaster_abc import ForecasterABC


class TimeOfUseMPCController(ControllerABC):
    """
    Controller which uses Model Predictive Control (MPC) to optimize the
    operation of a storage system based on time-of-use pricing and load
    forecasts (charge when prices are low, discharge when high).

    Args:
        load_forecaster: Forecaster for the load.
        price_forecaster: Forecaster for the prices (expects €/kWh).
        time_delta_seconds: The length of a time step in seconds.
        storage_model_power: The charge and discharge maximum power of the storage system in kW.
        storage_model_capacity: The energy capacity of the storage system in kWh.
        forecast_length: The number of time steps to forecast for the
            optimization, including the current time step. Also defines the
            length of the optimisation horizon.
        storage_label: The label of the storage system to be controlled.
    """
    def __init__(self,
                 load_forecaster: ForecasterABC,
                 price_forecaster: ForecasterABC,
                 time_delta_seconds: float,
                 storage_model_power: float,
                 storage_model_capacity: float,
                 storage_label: str,
                 forecast_length: int = 24 * 4) -> None:
        if forecast_length < 1:
            raise ValueError('forecast_length must be at least 1.')
        self._time_delta_hours = time_delta_seconds / 3600
        self._load_forecaster = load_forecaster
        self._price_forecaster = price_forecaster
        self._storage_model_power = storage_model_power
        self._storage_model_capacity = storage_model_capacity
        self._forecast_length = forecast_length
        self._storage_label = storage_label
        self._solver = pyo.SolverFactory('ipopt')

    def get_action(self, state: State) -> Tuple[Dict[str, float], Any]:
        self._load_forecaster.fit(state)
        load_horizon = [
            self._load_forecaster.get_current_value(),
            *list(self._load_forecaster.predict(forecast_length=self._forecast_length - 1)),
        ]
        self._price_forecaster.fit(state)
        price_horizon = [
            self._price_forecaster.get_current_value(),
            *list(self._price_forecaster.predict(forecast_length=self._forecast_length - 1)),
        ]
        storage_soc = state.components_states[self._storage_label]['soc']
        problem_formulation = build_optimization_problem(
            load=np.array(load_horizon) * -1,
            price=price_horizon,
            soc=storage_soc,
            power=self._storage_model_power,
            capacity=self._storage_model_capacity,
            time_delta_hours=self._time_delta_hours,
        )
        self._solver.solve(problem_formulation, tee=True)
        optimal_action = pyo.value(problem_formulation.power[0])
        control_action = optimal_action * -1

        return {self._storage_label: control_action}, None


def build_optimization_problem(
        load: GenericSequence,
        price: GenericSequence,
        soc: float,
        power: float,
        capacity: float,
        time_delta_hours: float,
) -> pyo.Model:
    """
    In contrast to the definitions in NRGISE, here we consider charging as positive power and discharging as negative
    power. Also, the load has positive power values.
    """
    time = range(len(load))
    soc_time = range(len(load) + 1)
    max_power_charge = power
    max_power_discharge = power * -1
    energy_capacity = capacity
    max_soc = 1
    min_soc = 0
    soc_init = soc

    m = pyo.AbstractModel()
    m.power = pyo.Var(time, domain=pyo.Reals, bounds=(max_power_discharge, max_power_charge))
    m.soc = pyo.Var(soc_time, bounds=(min_soc, max_soc))

    def obj_expression(m: Any) -> Any:
        return sum([price[i] * pyo.log(1 + pyo.exp((m.power[i] + load[i]))) for i in time])

    m.OBJ = pyo.Objective(rule=obj_expression, sense=pyo.minimize)

    def soc_start_rule(m: Any) -> Any:
        return m.soc[0] == soc_init

    m.soc_start = pyo.Constraint(rule=soc_start_rule)

    def soc_constraint_rule(m: Any, i: int) -> Any:
        return m.soc[i + 1] == time_delta_hours * (m.power[i]) / energy_capacity + m.soc[i]

    m.soc_constraints = pyo.Constraint(time, rule=soc_constraint_rule)

    return m.create_instance()
