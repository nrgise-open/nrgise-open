import warnings

from nrgise.common.types import UnivariateSequence
from nrgise.components.power_profile import PowerProfile


def check_pv_profile(power_profile: UnivariateSequence) -> None:
    if sum(power_profile) < 0:
        warning_msg = (f'The sum of the given `power_profile` is {sum(power_profile)}. '
                       f'Usually, a PV system produces power. Therefore, the power profile should be positive')
        warnings.warn(warning_msg)

class Pv(PowerProfile):
    """
    A more concrete implementation of `PowerProfileComponent` which represents a PV system (values per time step in kW).

    Args:
        power_profile: A profile containing the amount of power (kW) produced by the Pv System. These values are usually positive.
        label: An unique identifier for the component.
    """
    def __init__(
            self,
            label: str,
            power_profile: UnivariateSequence,
    ):
        super().__init__(label=label, power_profile=power_profile)
        check_pv_profile(power_profile)
