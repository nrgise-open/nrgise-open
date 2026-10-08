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
            thermal_storage_label: str,
            thermal_storage_power: float,
            cop: float,
            heat_bus: Bus,
    ) -> None:
        if cop <= 0:
            raise ValueError("`cop` must be greater than zero.")

        self._power_to_heat_label = power_to_heat_label
        self._thermal_storage_label = thermal_storage_label
        self._thermal_storage_power = thermal_storage_power
        self._cop = cop
        self._heat_bus = heat_bus

    def get_action(self, state: State) -> tuple[ControlAction, Any]:
        """
        Caution: Generated methodological logic; verification needed.

        Method summary:
        - Charge for the first 12 steps and discharge for the final 12 steps.
        - Use power-to-heat generation to keep the heat bus balanced.

        Reasoning:
        - Charging adds to heat demand, while discharging reduces heat demand.

        Assumptions and Limitations:
        - The simulation has 24 one-hour steps and the storage can apply the scheduled power.
        - COP is constant and heat demand remains above discharge power.

        Confidence Level: High
        """
        heat_demand = max(0.0, -state.uncontrolled_power_balance_per_bus[self._heat_bus])
        storage_power = (
            -self._thermal_storage_power
            if state.time_step < 12
            else self._thermal_storage_power
        )

        power_to_heat_output = heat_demand - storage_power
        electrical_input_power = power_to_heat_output / self._cop

        return {
            self._power_to_heat_label: electrical_input_power,
            self._thermal_storage_label: storage_power,
        }, None
