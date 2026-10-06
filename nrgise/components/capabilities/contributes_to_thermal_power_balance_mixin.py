# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from abc import ABC, abstractmethod

from nrgise.components.component_abc import ComponentABC


class ContributesToThermalPowerBalanceMixin(ComponentABC, ABC):
    """Capability for components with an uncontrolled thermal power contribution."""

    @abstractmethod
    def uncontrolled_thermal_power_contribution(self) -> float:
        """Return the thermal power contribution in kW for the current time step.

        Positive values supply the thermal system; negative values consume
        thermal power.
        """
        pass
