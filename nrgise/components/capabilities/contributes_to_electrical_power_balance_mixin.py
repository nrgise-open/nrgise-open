# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from abc import ABC, abstractmethod

from nrgise.components.component_abc import ComponentABC


class ContributesToElectricalPowerBalanceMixin(ComponentABC, ABC):
    """Capability for components with an uncontrolled electrical power contribution."""

    @abstractmethod
    def uncontrolled_electrical_power_contribution(self) -> float:
        """Return the electrical power contribution in kW for the current time step.

        Positive values supply the electrical system; negative values consume
        electrical power.
        """
        pass
