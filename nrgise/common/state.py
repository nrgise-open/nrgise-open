# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from dataclasses import dataclass
from typing import Any, Callable, List, Type, TypeVar, Union

import pandas as pd

from nrgise.components.capabilities.contributes_to_electrical_power_balance_mixin import (
    ContributesToElectricalPowerBalanceMixin,
)
from nrgise.components.capabilities.contributes_to_thermal_power_balance_mixin import (
    ContributesToThermalPowerBalanceMixin,
)
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
    - Information about the uncontrolled electrical and thermal power contributions of components. These contributions
        happen independently of system control and are kept in separate balances.
    """

    time_step: int
    date_time: pd.Timestamp
    uncontrolled_electrical_power_balance: float
    uncontrolled_electrical_power_contribution_per_component: dict[str, float]
    uncontrolled_thermal_power_balance: float
    uncontrolled_thermal_power_contribution_per_component: dict[str, float]
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

    uncontrolled_electrical_power_contributions, uncontrolled_electrical_power_balance = (
        _get_uncontrolled_power_contributions(
            components,
            ContributesToElectricalPowerBalanceMixin,
            lambda component: component.uncontrolled_electrical_power_contribution(),
        )
    )
    uncontrolled_thermal_power_contributions, uncontrolled_thermal_power_balance = (
        _get_uncontrolled_power_contributions(
            components,
            ContributesToThermalPowerBalanceMixin,
            lambda component: component.uncontrolled_thermal_power_contribution(),
        )
    )

    # Making the inclusion optional for performance reasons
    components_state = {}
    if include_components_state:
        components_state = _get_components_state(components)

    return State(
        time_step=time_step,
        date_time=date_time,
        uncontrolled_electrical_power_balance=uncontrolled_electrical_power_balance,
        uncontrolled_electrical_power_contribution_per_component=uncontrolled_electrical_power_contributions,
        uncontrolled_thermal_power_balance=uncontrolled_thermal_power_balance,
        uncontrolled_thermal_power_contribution_per_component=uncontrolled_thermal_power_contributions,
        components_states=components_state,
    )


ContributionMixinT = TypeVar(
    'ContributionMixinT',
    ContributesToElectricalPowerBalanceMixin,
    ContributesToThermalPowerBalanceMixin,
)


def _get_uncontrolled_power_contributions(
        components: List[ComponentABC],
        contribution_mixin: Type[ContributionMixinT],
        get_contribution: Callable[[ContributionMixinT], float],
        ) -> tuple[dict[str, float], float]:
    contributions_per_component: dict[str, float] = {}
    power_balance = 0.0
    for component in components:
        if isinstance(component, contribution_mixin):
            component_power_contribution = get_contribution(component)
            contributions_per_component[component.label] = component_power_contribution
            power_balance += component_power_contribution
    return contributions_per_component, power_balance


def _get_components_state(components: List[ComponentABC]) -> dict:
    results = {}
    for component in components:
        if isinstance(component, PublishesStateMixin):
            results[component.label] = component.get_state()
    return results
