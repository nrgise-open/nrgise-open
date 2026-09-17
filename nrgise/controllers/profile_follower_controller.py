from collections.abc import Iterable
from typing import Any, Dict, Optional, Tuple

from nrgise.common.state import State
from nrgise.controllers.controller_abc import ControllerABC


class ProfileFollowerController(ControllerABC):
    """
    The control actions are considered fixed and are defined by the profile given to the controller. Once all actions
    of the profile are executed, the profile starts again.

    Args:
        control_profile: Sequence of control actions (power in kW) which will be requested.
        storage_label: Label of the Controllable.
    """

    def __init__(self,
                 control_profile: Iterable[float],
                 storage_label: str) -> None:
        self._storage_label = storage_label
        self._control_profile = tuple(control_profile)
        self._action_pointer = 0

    def get_action(self, _: Optional[State] = None) -> Tuple[Dict[str, float], Any]:
        action = self._control_profile[self._action_pointer]
        self._action_pointer = (self._action_pointer + 1) % len(self._control_profile)
        return {self._storage_label: action}, None
