from dataclasses import dataclass
from typing import Any, List, Union

import pandas as pd

from nrgise.components.capabilities.contributes_to_power_balance_mixin import ContributesToPowerBalanceMixin
from nrgise.components.capabilities.publishes_state_mixin import PublishesStateMixin
from nrgise.components.component_abc import ComponentABC


@dataclass(frozen=True)
class State:
    """
    Describes the state of the EnergySystem.

    It is generated in each simulation time step and used by the controllers
    as decision criteria. Later, the information from the state per time step
    is available
    in the simulation results.

    The state contains:

    - Information about the time step and datetime of the state.
    - Information about the state of all components of the EnergySystem which implement `PublishesStateMixin`
        interface. The state of the components is published by their implementation of `get_state()`.
    - Information about the uncontrolled power contribution of a component. An uncontrolled power contribution happens
        no matter how the system is controlled. For example by a load or a pv
        component. Components implementing `ContributesToPowerBalanceMixin` provide
        this information.
    """

    time_step: int
    uncontrolled_power_balance: float
    uncontrolled_power_contribution_per_component: dict[str, float]
    components_states: dict
    date_time: pd.Timestamp

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError as err:
            raise KeyError(f"{item} not found in {self.__class__.__name__}") from err


def build_state(components: List[ComponentABC],
                time_step: int,
                date_time: Union[pd.Timestamp, None] = None,
                include_components_state: bool = True,
                ) -> State:
    """
    Helper function to build the `State` used by the `EnergySystem` in each time step.
    """
    if date_time is None:
        date_time = pd.Timestamp.now()
    date_time = pd.Timestamp(date_time)

    uncontrolled_power_contribution_per_component, uncontrolled_power_balance = _get_uncontrolled_power_contributions(components)

    # Making the inclusion optional for performance reasons
    components_state = {}
    if include_components_state:
        components_state = _get_components_state(components)

    return State(
        time_step=time_step,
        date_time=date_time,
        uncontrolled_power_balance=uncontrolled_power_balance,
        uncontrolled_power_contribution_per_component=uncontrolled_power_contribution_per_component,
        components_states=components_state,
    )


def _get_uncontrolled_power_contributions(components: List[ComponentABC]) -> tuple[dict[str, float], float]:
    """
    Calculates each component's uncontrolled power contribution and the resulting uncontrolled power balance during the
    defined `time_step`.
    """
    uncontrolled_power_contribution_per_component: dict[str, float] = {}
    uncontrolled_power_balance = 0.0
    for component in components:
        if isinstance(component, ContributesToPowerBalanceMixin):
            components_power_contribution = component.uncontrolled_power_contribution()
            uncontrolled_power_contribution_per_component[component.label] = components_power_contribution
            uncontrolled_power_balance += components_power_contribution
    return uncontrolled_power_contribution_per_component, uncontrolled_power_balance


def _get_components_state(components: List[ComponentABC]) -> dict:
    results = {}
    for component in components:
        if isinstance(component, PublishesStateMixin):
            results[component.label] = component.get_state()
    return results
