from typing import Any

import numpy as np

from nrgise.components.capabilities.controllable_mixin import ControllableMixin
from nrgise.components.capabilities.data_profile_mixin import DataProfileMixin
from nrgise.components.capabilities.publishes_state_mixin import PublishesStateMixin
from nrgise.components.capabilities.time_step_aware_mixin import TimeStepAwareMixin
from nrgise.components.pv.pv import check_pv_profile


class PvCurtailable(DataProfileMixin, ControllableMixin, PublishesStateMixin, TimeStepAwareMixin):
    """
    Curtailable and therefore controllable photovoltaic (PV) system with a predefined generation power profile (kW).

    The component uses a predefined PV power profile to describe the maximum
    available generation at each time step. Actual power generation does not
    have to match the profile exactly: it may be lower, for example due to
    curtailment which can be defined by a *Controller*.

    Note that using this component requires a *Controller* which provides actions for this component.

    Args:
        label: Unique label.
        power_profile: Maximum available PV generation (kW) per time step.
            Note that the values are positive as they represent power supplied
            to the energy system.
    """
    def __init__(
            self,
            label: str,
            power_profile: np.ndarray,
        ) -> None:
        self._label = label
        self._data_profile = np.array(power_profile)
        self._time_step = 0
        check_pv_profile(power_profile)

    def reset(self) -> None:
        self._time_step = 0

    @property
    def label(self) -> str:
        return self._label

    def get_state(self) -> dict[str, Any]:
        """Return the predefined pv generation according to the data profile at the current time step.

        Returns:
            A dictionary containing the following keys:

                - ``generation``: The generation according to the data profile for this time step in kW.
        """
        return {'generation': self._data_profile[self._time_step]}

    def set_power_contribution(self, power: float) -> float:
        max_power_generation = float(self._data_profile[self._time_step])
        # Variable production is limited to power of profile, but must be positive
        return max(0.0, min(max_power_generation, power))

    @property
    def data_profile(self) -> np.ndarray:
        return self._data_profile

    @data_profile.setter
    def data_profile(self, data_profile: np.ndarray) -> None:
        self._data_profile = data_profile

    def handle_time_step_update(self, time_step: int) -> None:
        self._time_step = time_step
