# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
import numpy as np
import pandas as pd

from nrgise.common.types import GenericSequence, UnivariateSequence
from nrgise.components.capabilities.contributes_to_electrical_power_balance_mixin import (
    ContributesToElectricalPowerBalanceMixin,
)
from nrgise.components.capabilities.contributes_to_thermal_power_balance_mixin import (
    ContributesToThermalPowerBalanceMixin,
)
from nrgise.components.capabilities.data_profile_mixin import DataProfileMixin
from nrgise.components.capabilities.time_step_aware_mixin import TimeStepAwareMixin


# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
class _PowerProfile(DataProfileMixin, TimeStepAwareMixin):
    """
    Represents component that cannot be controlled and its power values (kW)
    are predefined by a power profile (for example a fixed solar generation or
    fixed load profile). Note that positive alues mean power is generated,
    whereas negative values mean power is consumed.

    Args:
        power_profile: A profile containing the amount of power (kW) served or
            consumed by the component for every time step.
        label: An unique identifier for the component.
    """

    def __init__(self,
                 label: str,
                 power_profile: UnivariateSequence) -> None:
        if isinstance(power_profile, pd.DataFrame):
            raise TypeError
        self._label = label
        self._power_profile = np.array(power_profile)
        self._time_step: int = 0

    def reset(self) -> None:
        self._time_step = 0

    def handle_time_step_update(self, time_step: int) -> None:
        self._time_step = time_step

    @property
    def _current_power_value(self) -> float:
        return float(self._power_profile[self._time_step])

    @property
    def data_profile(self) -> GenericSequence:
        return self._power_profile

    @data_profile.setter
    def data_profile(self, value: GenericSequence) -> None:
        self._power_profile = np.array(value)

    @property
    def label(self) -> str:
        return self._label

# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
class ElectricalPowerProfile(_PowerProfile, ContributesToElectricalPowerBalanceMixin):
    """An uncontrolled electrical power profile in kW."""

    def uncontrolled_electrical_power_contribution(self) -> float:
        return self._current_power_value

# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
class ThermalPowerProfile(_PowerProfile, ContributesToThermalPowerBalanceMixin):
    """An uncontrolled thermal power profile in kW_th."""

    def uncontrolled_thermal_power_contribution(self) -> float:
        return self._current_power_value
