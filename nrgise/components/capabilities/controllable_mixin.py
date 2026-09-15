from abc import ABC, abstractmethod

from nrgise.components.component_abc import ComponentABC


class ControllableMixin(ComponentABC, ABC):
    """
    Controllable components can receive requested power contributions from a `ControllerABC`.
    Note that the number of controllables in an `EnergySystem` must match the number of actions returned by the
    *Controller*. The action of the controller is a dict and the key
    must match the label of the controllable component. The matching is done by
    the `EnergySystem`. This way routing of actions is ensured when multiple
    controllables are present.
    """

    @abstractmethod
    def set_power_contribution(self, power: float) -> float:
        """
        Apply the requested power contribution (kW) for the current time step.

        Positive values add power to the energy system's power balance, while
        negative values consume power.

        The component should apply the requested power subject to its physical constraints
        and update its internal state accordingly. For example, a battery should
        update its state of charge based on the power actually charged or discharged.

        The method returns the power that was actually applied, which may differ
        from the requested value due to constraints such as state of charge, power
        limits, or efficiency losses.

        Args:
            power: The requested power contribution (kW) requested by the controller.

        Returns:
            The actual power contribution (kW) applied by the component during
                the time step. This may differ from the requested value if the
                requested power cannot be realized (e.g., requesting discharge from
                an empty battery).
        """
