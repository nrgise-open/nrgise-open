import warnings

from nrgise.common.types import UnivariateSequence
from nrgise.components.power_profile import PowerProfile


class Load(PowerProfile):
    """
    A more concrete implementation of `PowerProfileComponent` which represents a load (values per time step in kW).

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
        if sum(power_profile) > 0:
            warning_msg = (f'The sum of the given `power_profile` is {sum(power_profile)} and therefore positive. '
                           f'Usually, a load consumes power. Therefore, the power profile should be negative')
            warnings.warn(warning_msg)
