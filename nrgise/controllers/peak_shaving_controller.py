import warnings
from typing import Any, Dict, Tuple

from nrgise.common.state import State
from nrgise.controllers.controller_abc import ControllerABC


class PeakShavingController(ControllerABC):
    """
    Discharge if the `uncontrolled_power_balance` is more extreme as the
    `cut_off_power_value` (and charge if it is not).
    Note that the `uncontrolled_power_balance` is negative if the consumption
    is greater as the generation.
    Therefore, the `cut_off_power_value` should be negative as well.

    Args:
        cut_off_power_value: The *maximum* power value which should not be
            exceeded. Note that this value is usually negative, as consumption
            is defined by negative values!
        storage_label: Label of the storage to be controlled.
    """

    def __init__(self,
                 cut_off_power_value: float,
                 storage_label: str):
        self._storage_label = storage_label
        self._cut_off_power_value = cut_off_power_value

        if self._cut_off_power_value > 0:
            warning_msg = (f'The given `cut_off_power_value` is {self._cut_off_power_value} and therefore positive. '
                           f'Usually, a load consumes power and is negative. Therefore, the cut off power value '
                           f'should be negative too.')
            warnings.warn(warning_msg)


    def get_action(self, state: State) -> Tuple[Dict[str, float], Any]:
        controller_state = None
        # Positive means gaining power from the battery aka. discharging the battery
        # Meaning if the demand is greater, we are discharging.
        battery_power_setpoint = self._cut_off_power_value - state.uncontrolled_power_balance
        return {self._storage_label: battery_power_setpoint}, controller_state
