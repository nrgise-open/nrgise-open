from typing import Any, Dict, Tuple

from nrgise.common.state import State
from nrgise.controllers.controller_abc import ControllerABC


class SelfConsumptionController(ControllerABC):
    """
    Storage Controller which performs self consumption optimization.

    - Charge storage (negative action) when the power balance is positive, meaning there is more generation than consumption
    - Discharge storage (positive action) when the power balance is negative, meaning there is more consumption than generation

    Args:
        storage_label: Label of the storage to be controlled.
    """

    def __init__(self, storage_label: str):
        self._storage_label = storage_label

    def get_action(self, state: State) -> Tuple[Dict[str, float], Any]:
        controller_state = None
        control_action = -1 * state.uncontrolled_power_balance
        return {self._storage_label: control_action}, controller_state
