# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from typing import Any

from nrgise.common.state import State
from nrgise.common.types import Bus, ControlAction
from nrgise.controllers import ControllerABC


class HeatDemandController(ControllerABC):
    """Control a power-to-heat component to balance uncontrolled heat demand."""

    def __init__(
            self,
            power_to_heat_label: str,
            cop: float,
            heat_bus: Bus,
    ) -> None:
        if cop <= 0:
            raise ValueError("`cop` must be greater than zero.")

        self._power_to_heat_label = power_to_heat_label
        self._cop = cop
        self._heat_bus = heat_bus

    def get_action(self, state: State) -> tuple[ControlAction, Any]:
        heat_demand = max(0.0, -state.uncontrolled_power_balance_per_bus[self._heat_bus])
        electrical_input_power = heat_demand / self._cop

        return {self._power_to_heat_label: electrical_input_power}, None
