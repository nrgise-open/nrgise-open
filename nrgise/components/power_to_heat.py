# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from nrgise.common.constants import ELECTRICITY_BUS
from nrgise.common.types import Bus, PowerContribution
from nrgise.components.capabilities.controllable_mixin import ControllableMixin


class PowerToHeat(ControllableMixin):
    """Convert controlled electrical input power into thermal output power.

    The control action is interpreted as the non-negative amount of electrical
    power consumed by the component. The returned contribution is negative on
    the electrical bus and positive on the heat bus.

    Args:
        label: Unique identifier of the component.
        cop: Constant coefficient of performance, defined as thermal output
            power divided by electrical input power.
        electricity_bus: Bus from which electrical power is consumed.
        heat_bus: Bus to which thermal power is supplied.
    """

    def __init__(
            self,
            label: str,
            cop: float = 0.5,
            electricity_bus: Bus = ELECTRICITY_BUS,
            heat_bus: Bus = "heat",
    ) -> None:
        if cop <= 0:
            raise ValueError("`cop` must be greater than zero.")
        if electricity_bus == heat_bus:
            raise ValueError("`electricity_bus` and `heat_bus` must be different.")

        self._label = label
        self._cop = cop
        self._electricity_bus = electricity_bus
        self._heat_bus = heat_bus

    def set_power_contribution(self, power: float) -> PowerContribution:
        """
        Args:
            power: Non-negative electrical input power requested in kW.

        Returns:
            Negative electrical and positive thermal power contributions in kW.
        """
        if power < 0:
            raise ValueError("Power-to-heat input power must not be negative.")

        return {
            self._electricity_bus: -power,
            self._heat_bus: power * self._cop,
        }

    def reset(self) -> None:
        """Reset the stateless component."""

    @property
    def label(self) -> str:
        return self._label

    @property
    def cop(self) -> float:
        return self._cop

    @property
    def electricity_bus(self) -> Bus:
        return self._electricity_bus

    @property
    def heat_bus(self) -> Bus:
        return self._heat_bus
