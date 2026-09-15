from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

from nrgise.common.helper import flatten_dict
from nrgise.common.state import State
from nrgise.controllers.controller_abc import ControllerABC
from nrgise.energy_system import EnergySystem


@dataclass
class SimulationStepResult:
    """
    Contains all information of a single simulation step.
    Will be used to store simulation results later.
    """
    time_step: int
    date_time: pd.Timestamp
    uncontrolled_power_balance: float
    uncontrolled_power_contribution_per_component: Dict[str, float]
    components_states: Dict
    grid_builder_usage: float
    power_requested: Union[float, Dict[str, float]]
    power_applied: Union[float, Dict[str, float]]
    additional_control_info: Any

SimulationHook = Callable[['Simulation', 'SimulationStepResult'], None]

class Simulation:
    """
    The `Simulation` iterates over all simulation time steps of the `EnergySystem`, asks
    the controller for an action, applies the action through the
    `EnergySystem`, balances any remaining power via the grid builder, and
    stores one `SimulationStepResult` per step.

    For a detailed sequence diagram and step-by-step explanation of the
    simulation flow, see the user guide section "Simulation Flow".

    Args:
        energy_system: The EnergySystem to simulate.
        controller: The `ControllerABC` used as EMS.
    """

    def __init__(
            self,
            energy_system: EnergySystem,
            controller: Optional[ControllerABC] = None,
    ):
        self._energy_system = energy_system
        self._controller = controller
        self._simulation_results: List[SimulationStepResult] = []
        self._hooks: List[SimulationHook] = []

    def run(self) -> pd.DataFrame:
        """
        Run the simulation by looping through the energy system time index.

        For each time step, this method:

        1. queries the controller for a control action by passing the current `State`,
        2. advances the `EnergySystem` by one step by applying the action,
        3. balances remaining power via the grid builder,
        4. records the resulting `SimulationStepResult`, and
        5. executes registered simulation hooks.
        6. updates the `State` for the next time step.

        Returns:
            Simulation results as a Pandas DataFrame indexed by `date_time`.
        """
        grid_builder = self._energy_system.get_grid_builder()

        initial_state = self._energy_system.reset()
        state = initial_state
        done = False

        while not done:
            if self._controller:
                power_requested, additional_control_info = self._controller.get_action(state)
            else:
                power_requested, additional_control_info = {}, None
            power_applied_to_controllables, next_state, done = self._energy_system.simulate_one_time_step(
                power_requested)

            power_balance = state.uncontrolled_power_balance + sum(power_applied_to_controllables.values())
            power_required_from_grid_builder = -1 * power_balance
            power_taken_from_grid_builder = grid_builder.supply_power(power_required_from_grid_builder)
            if power_taken_from_grid_builder != power_required_from_grid_builder:
                raise ValueError('Power could not be balanced by the grid builder.')
            single_simulation_step_result = self._build_single_simulation_step_result(
                state,
                power_requested,
                power_applied_to_controllables,
                power_taken_from_grid_builder,
                additional_control_info,
            )
            self._simulation_results.append(single_simulation_step_result)
            self._run_hooks(simulation_step_result=single_simulation_step_result)
            state = next_state  # type: ignore

        return self._post_process_simulation_results(self._simulation_results)

    def register_hook(self, func: SimulationHook) -> None:
        """
        Register a function to be executed after each completed simulation step
        (aka. hook). A hook can be used to inject custom logic into the
        simulation loop.

        Required function signature:

        `def function_defining_the_hook(simulation: Simulation, step_result: SimulationStepResult) -> None`

        Args:
            func: Hook function matching `SimulationHook`.
        """
        self._hooks.append(func)

    def _run_hooks(self, simulation_step_result: SimulationStepResult) -> None:
        for func in self._hooks:
            func(self, simulation_step_result)


    @staticmethod
    def _post_process_simulation_results(simulation_results: List[SimulationStepResult]) -> pd.DataFrame:
        flat_simulation_results = [flatten_dict(vars(item)) for item in simulation_results]
        result_df = pd.DataFrame(flat_simulation_results)
        return result_df.set_index('date_time')

    @staticmethod
    def _build_single_simulation_step_result(state: State,
                                             power_requested: dict[str, float],
                                             power_applied: dict[str, float],
                                             power_taken_from_grid_builder: float,
                                             additional_control_info: Any) -> SimulationStepResult:
        """
        A single simulation step results contains all information necessary to do postprocessing (economics, plots, etc.)
        of the simulation.

        It contains the state fields of one time step plus:
        - the control action taken
        - the resulting grid usage
        """

        # In case only one controllable is used, we convert the list into a scalar in order to make postprocessing of
        # the results more convenient
        result_power_applied: Union[float, Dict[str, float]]
        result_power_requested: Union[float, Dict[str, float]]
        if len(power_applied) == 1 and len(power_requested) == 1:
            result_power_applied = sum(power_applied.values())
            result_power_requested = sum(power_requested.values())
        elif len(power_applied) == 0 and len(power_requested) == 0:
            result_power_applied = 0.0
            result_power_requested = 0.0
        else:
            result_power_applied = power_applied
            result_power_requested = power_requested

        return SimulationStepResult(
            # Includes State information
            time_step=state.time_step,
            date_time=state.date_time,
            uncontrolled_power_balance=state.uncontrolled_power_balance,
            uncontrolled_power_contribution_per_component=state.uncontrolled_power_contribution_per_component,
            components_states=state.components_states,
            grid_builder_usage=power_taken_from_grid_builder,
            power_requested=result_power_requested,
            power_applied=result_power_applied,
            additional_control_info=additional_control_info,
        )
