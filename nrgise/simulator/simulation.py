# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

from nrgise.common.constants import ELECTRICITY_BUS
from nrgise.common.helper import flatten_dict
from nrgise.common.state import State
from nrgise.common.types import Bus, ControlAction, PowerContribution
from nrgise.controllers.controller_abc import ControllerABC
from nrgise.energy_system import EnergySystem


# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
@dataclass
class SimulationStepResult:
    """
    Contains all information of a single simulation step.
    Will be used to store simulation results later.
    """
    time_step: int
    date_time: pd.Timestamp
    uncontrolled_power_balance_per_bus: Dict[Bus, float]
    uncontrolled_power_contribution_per_component_and_bus: Dict[str, PowerContribution]
    power_balance_per_bus: Dict[Bus, float]
    components_states: Dict
    grid_builder_usage: float
    power_requested: Union[float, ControlAction]
    power_applied: Union[float, Dict[str, PowerContribution]]
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

            power_balance_per_bus = (
                self._calculate_power_balance_per_bus(state, power_applied_to_controllables)
            )
            electrical_power_balance = power_balance_per_bus[ELECTRICITY_BUS]
            electrical_power_required_from_grid_builder = -1 * electrical_power_balance
            power_taken_from_grid_builder = grid_builder.supply_power(electrical_power_required_from_grid_builder)
            if power_taken_from_grid_builder != electrical_power_required_from_grid_builder:
                raise ValueError('Power could not be balanced by the grid builder.')

            single_simulation_step_result = self._build_single_simulation_step_result(
                state,
                power_requested,
                power_applied_to_controllables,
                power_balance_per_bus,
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

    # Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
    @staticmethod
    def _build_single_simulation_step_result(state: State,
                                              power_requested: ControlAction,
                                              power_applied: dict[str, PowerContribution],
                                              power_balance_per_bus: dict[Bus, float],
                                              power_taken_from_grid_builder: float,
                                              additional_control_info: Any) -> SimulationStepResult:
        """
        A single simulation step results contains all information necessary to do postprocessing (economics, plots, etc.)
        of the simulation.

        It contains the state fields of one time step plus:
        - the control action taken
        - the resulting grid usage
        """

        # Convert to scalar if only one controllable simulated.
        result_power_requested: Union[float, ControlAction]
        if len(power_requested) == 1:
            result_power_requested = sum(power_requested.values())
        elif len(power_requested) == 0:
            result_power_requested = 0.0
        else:
            result_power_requested = power_requested

        applied_contributions = [
            contribution
            for component_contributions in power_applied.values()
            for contribution in component_contributions.values()
        ]

        result_power_applied: Union[float, Dict[str, PowerContribution]]
        if len(power_requested) == 1 and len(applied_contributions) == 1:
            result_power_applied = applied_contributions[0]
        elif len(power_requested) == 0 and len(applied_contributions) == 0:
            result_power_applied = 0.0
        else:
            result_power_applied = power_applied

        # The electricity balance is already represented with the opposite sign by grid_builder_usage.
        reported_power_balance_per_bus = {
            bus: power
            for bus, power in power_balance_per_bus.items()
            if bus != ELECTRICITY_BUS
        }

        return SimulationStepResult(
            # Includes State information
            time_step=state.time_step,
            date_time=state.date_time,
            uncontrolled_power_balance_per_bus=state.uncontrolled_power_balance_per_bus,
            uncontrolled_power_contribution_per_component_and_bus=(
                state.uncontrolled_power_contribution_per_component_and_bus
            ),
            power_balance_per_bus=reported_power_balance_per_bus,
            components_states=state.components_states,
            grid_builder_usage=power_taken_from_grid_builder,
            power_requested=result_power_requested,
            power_applied=result_power_applied,
            additional_control_info=additional_control_info,
        )

    # Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
    @staticmethod
    def _calculate_power_balance_per_bus(
            state: State,
            power_applied: dict[str, PowerContribution],
    ) -> dict[Bus, float]:
        power_balance_per_bus = dict(state.uncontrolled_power_balance_per_bus)

        for power_contribution in power_applied.values():
            for power_bus, power in power_contribution.items():
                power_balance_per_bus[power_bus] = power_balance_per_bus.get(power_bus, 0.0) + power

        return power_balance_per_bus
