from typing import Dict, List, Optional, Type, TypeVar, cast

import numpy as np
import pandas as pd

from nrgise.common.helper import get_time_delta_seconds
from nrgise.common.state import State, build_state
from nrgise.components.capabilities.controllable_mixin import ControllableMixin
from nrgise.components.capabilities.data_profile_mixin import DataProfileMixin
from nrgise.components.capabilities.time_step_aware_mixin import TimeStepAwareMixin
from nrgise.components.component_abc import ComponentABC
from nrgise.components.grid_builder.grid_builder_abc import GridBuilderABC
from nrgise.tools import stretch_data_profile


class EnergySystem:
    """
    The `EnergySystem` represents the main container for the local energy system to be modeled.
    All components (e.g. storage, grid, pv_system) of the system to be modelled have to be added
    to the `EnergySystem`. The concept of the EnergySystem
    implemented here is based on the basic ideas of an EnergySystem in oemof
    (see https://oemof-solph.readthedocs.io/en/latest/usage.html#set-up-an-energy-system).

    Args:
        time_index: Pandas DatetimeIndex which defines the datetime range looped over when running a simulation.
    """

    def __init__(self, time_index: pd.DatetimeIndex):
        self._time_delta_seconds: int = int(get_time_delta_seconds(time_index))
        # Converting `time_index` to numpy internally as indexing pd.DatetimeIndex is slow
        self._time_index: np.ndarray = time_index.to_numpy()
        self._time_step = 0
        self._components: List[ComponentABC] = []
        self._controllable_components: Dict[str, ComponentABC] = {}

    def add_components(self, *args: ComponentABC) -> None:
        """
        Adds one or more `Component` to the EnergySystem.

        Args:
            args: One or more components to add to the EnergySystem.

        Example:
            ```python
            es.add_components(grid, load, aging_battery, pv_system)
            ```
        """
        for component in args:
            if self.get_component_by_label(component.label) is not None:
                raise ValueError(f'Labels must be unique. There is already a component with label {component.label} in '
                                 f'the energy system.')
            self._components.append(component)

    def get_component_by_label(self, label: str) -> Optional[ComponentABC]:
        """
        Returns a component which matches the `label`.

        Args:
            label: The label to search for.
        Returns:
            The Component found or None
        """
        for component in self._components:
            if component.label == label:
                return component
        return None

    def get_grid_builder(self) -> GridBuilderABC:
        """
        Returns the `GridBuilder` of the EnergySystem. Could be `GridBuilder`, `Grid`, `Generator`, ...

        Returns:
            The grid builder.
        """
        grid_builders = [component for component in self._components if isinstance(component, GridBuilderABC)]
        if len(grid_builders) != 1:
            raise ValueError('Currently only EnergySystems with one `GridBuilder` are supported.')
        return grid_builders[0]

    T = TypeVar('T')

    def get_components_by_instance(self, instance: Type[T]) -> list[T]:
        """
        Searches self.components for all objects of type `instance` and returns them as a list.

        Args:
            instance: instance to search for e.g. `Battery`
        Returns:
            List of objects of type of the `instance`
        """
        return [component for component in self._components if isinstance(component, instance)]

    def reset(self) -> State:
        """
        Resets the EnergySystem by:

        - Setting controllable components which receive actions from a controller
        - Calling `reset()` on all components of this EnergySystem which implement a `reset()` method.
        - Setting the time to 0

        Returns:
            The initial State of the EnergySystem
        """
        self._set_controllable_components()
        for component in self._components:
            component.reset()
        self._check_components_data_profile_length()
        self._update_time(0)
        return self._get_state()

    def simulate_one_time_step(self, action: dict[str, float]) -> tuple[dict[str, float], Optional[State], bool]:
        """
        This method is used by the `Simulation` and can be considered the core method which performs the simulation of
        the energy system. It executes:

        1. The action is dispatched to the corresponding controllable
            components. The actual power contribution is returned
            (note that this can differ from the requested action due to physical constraints of the controllable components).
        2. The time step is incremented. This time step update is propagated to all components which implement
            `TimeStepAwareMixin`
            (e.g. if they contain a data profile which must be stepped through)
        3. By performing the previous steps, the power system is now in a new `State`. This is queried. In addition,
            information is requested if the simulation has reached its end.

        Returns:
            The power contribution actually deliverd by the controllable in this simulation step.
            State for next simulation step (or None if the simulation is done)
            Is the simulation done or not? Defined by if the time step exceeds the last time index of the EnergySystem.
        """
        power_contribution_per_controllable = self._perform_action(action)
        simulation_done: bool = self._update_time(self._time_step + 1)
        next_state: Optional[State] = None if simulation_done else self._get_state()
        return power_contribution_per_controllable, next_state, simulation_done

    def stretch_time(self, target_end_date: pd.Timestamp) -> None:
        """Extend the time index and components implementing `DataProfileMixin` to a `target_end_date`.

        Existing data profiles are repeated until the target date. This is
        useful for simulations over a longer period than the available input
        data, for example when investigating aging effects.

        Args:
            target_end_date: Timestamp through which the profiles are repeated.
        """
        date_time_index = pd.DatetimeIndex(self._time_index)
        if target_end_date < date_time_index[-1]:
            raise ValueError('`target_end_date` passed is before end of original `time_index`')

        target_date_time_index = pd.date_range(
            start=date_time_index[0],
            end=target_end_date,
            freq=f"{self._time_delta_seconds}s",
        )
        for component in self._components:
            if isinstance(component, DataProfileMixin):
                component.data_profile, _ = stretch_data_profile(
                    component.data_profile,
                    date_time_index,
                    target_end_date,
                )
        self._time_index = target_date_time_index.to_numpy()


    def _perform_action(self, action: dict[str, float]) -> dict[str, float]:
        """
        Forwards the actions to be done to the controllables which perform the action (most likely
        storages). This causes a change in the EnergySystem (or at least in the controllable_components which received
        the action - most likely the storages).

        Args:
            action: Dict of actions to perform.
        Returns:
            Dict of power contributions from the controllables.
        """
        if len(action) != len(self._controllable_components):
            raise ValueError('Actions and Controllable Components must be of the same length. One action per '
                             'controllable component.')
        power_contributions = {}
        for controllable_label, controllable_action in action.items():
            component = self._controllable_components[controllable_label]
            controllable = cast(ControllableMixin, component)
            power_contribution = controllable.set_power_contribution(controllable_action)
            power_contributions[controllable_label] = power_contribution

        return power_contributions

    def _get_state(self) -> State:
        """
        Returns the current state of the whole EnergySystem. This state can be used to decide on control
        actions

        Returns:
            The state of the EnergySystem
        """
        return build_state(self._components, self._time_step, self._time_index[self._time_step])

    def _update_time(self, time_step: int) -> bool:
        """
        Updates the `time_step` of the EnergySystem. the `time_step` is taken as an orientation where you are
        currently located in the data profiles of the EnergySystem.
        """
        self._time_step = time_step
        simulation_done: bool = self._is_simulation_done()
        if not simulation_done:
            self._propagate_time_step_update()
        return simulation_done

    def _set_controllable_components(self) -> None:
        """
        Sets the components of the `EnergySystem` which can be controlled and thus are able to receive and respond to
        actions. All components which have a `set_power` attribute (or function) are set as `controllable` and
        therefore receive actions.
        """
        self._controllable_components = {
            component.label: component
            for component in self._components
            if isinstance(component, ControllableMixin)
        }

    def _is_simulation_done(self) -> bool:
        # If time step exceeds last time index --> done
        return bool(self._time_step >= len(self._time_index))

    def _propagate_time_step_update(self) -> None:
        """
        Notifies components (which are effected by the time_step update) about the time_step update.
        """
        components_to_update = [
            component for component in self._components
            if isinstance(component, TimeStepAwareMixin)
        ]
        for component in components_to_update:
            component.handle_time_step_update(self._time_step)

    def _check_components_data_profile_length(self) -> None:
        """
        Raises an exception if not all components have the same data profile length (plus the same length of the
        `time_index` of the `EnergySystem`.
        """

        for component in self._components:
            if isinstance(component, DataProfileMixin) and len(component.data_profile) != len(self._time_index):
                raise ValueError('Data Profiles passed to components of the EnergySystem are not of equal length.')

    @property
    def components(self) -> List[ComponentABC]:
        return self._components

    @property
    def time_index(self) -> np.ndarray:
        return self._time_index

    @property
    def controllable_components(self) -> dict[str, ComponentABC]:
        return self._controllable_components

    @property
    def time_delta_seconds(self) -> int:
        return self._time_delta_seconds
