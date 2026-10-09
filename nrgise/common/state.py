from dataclasses import dataclass
from typing import Any, List, Union

import pandas as pd

from nrgise.common.constants import ELECTRICITY_BUS
from nrgise.common.types import Bus, PowerContribution
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
    - Information about uncontrolled power contributions per bus. These contributions happen independently of system
        control.
    """

    time_step: int
    date_time: pd.Timestamp
    uncontrolled_power_balance_per_bus: dict[Bus, float]
    uncontrolled_power_contribution_per_component_and_bus: dict[str, PowerContribution]
    components_states: dict

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

    power_balances, power_contributions, components_states = _get_state_values(
        components,
        include_components_state,
    )

    return State(
        time_step=time_step,
        date_time=date_time,
        uncontrolled_power_balance_per_bus=power_balances,
        uncontrolled_power_contribution_per_component_and_bus=power_contributions,
        components_states=components_states,
    )

# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
def _get_state_values(
        components: List[ComponentABC],
        include_components_state: bool,
        ) -> tuple[dict[Bus, float], dict[str, PowerContribution], dict]:
    power_balances = {ELECTRICITY_BUS: 0.0}
    power_contributions: dict[str, PowerContribution] = {}
    components_states = {}

    for component in components:
        if isinstance(component, ContributesToPowerBalanceMixin):
            component_power_contributions = dict(component.uncontrolled_power_contributions())
            power_contributions[component.label] = component_power_contributions
            for power_bus, power_contribution in component_power_contributions.items():
                power_balances[power_bus] = power_balances.get(power_bus, 0.0) + power_contribution

        if include_components_state and isinstance(component, PublishesStateMixin):
            components_states[component.label] = component.get_state()

    return power_balances, power_contributions, components_states
