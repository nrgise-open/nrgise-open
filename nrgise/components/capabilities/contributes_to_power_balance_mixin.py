from abc import ABC, abstractmethod

from nrgise.components.component_abc import ComponentABC


class ContributesToPowerBalanceMixin(ComponentABC, ABC):
    """
    Mixin for components with an uncontrollable power contribution.

    Components implementing this mixin provide a fixed power contribution (kW) for
    each simulation time step. Unlike `ControllableMixin` components, this
    contribution cannot be influenced by the controller and is therefore
    treated as a fixed part of the system power balance.

    Typical examples are electrical loads, photovoltaic systems, or any other
    component whose power is determined externally rather than by control
    actions.

    During state construction, the EnergySystem queries
    `uncontrolled_power_contribution()` and stores the value in the global
    `State`. The controller receives this information as part of the
    system state, and the contribution is later combined with the power
    provided by controllable components to determine the total system power
    balance.

    **Positive values represent power supplied to the energy system, while
    negative values represent power consumed from it.**
    """

    @abstractmethod
    def uncontrolled_power_contribution(self) -> float:
        """
        Returns:
            The uncontrollable power contribution in kW for the current time step.
        """
        pass
