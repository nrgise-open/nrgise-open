import warnings

from nrgise.common.constants import ELECTRICITY_BUS
from nrgise.common.types import UnivariateSequence
from nrgise.components.power_profile import PowerProfile


def _warn_if_profile_sum_is_positive(power_profile: UnivariateSequence, unit: str) -> None:
    profile_sum = sum(power_profile)
    if profile_sum > 0:
        warning_msg = (f'The sum of the given `power_profile` is {profile_sum} {unit} and therefore positive. '
                       'Usually, a load consumes power. Therefore, the power profile should be negative')
        warnings.warn(warning_msg)

# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
class Load(PowerProfile):
    """
    An electrical load whose demand values are negative and expressed in kW.

    Args:
        power_profile: An electrical demand profile in kW. Values are usually negative.
        label: An unique identifier for the component.
    """
    def __init__(
            self,
            label: str,
            power_profile: UnivariateSequence,
            power_bus: str = ELECTRICITY_BUS
    ):
        super().__init__(label=label, power_profile=power_profile, power_bus=power_bus)
        _warn_if_profile_sum_is_positive(power_profile, 'kW')
