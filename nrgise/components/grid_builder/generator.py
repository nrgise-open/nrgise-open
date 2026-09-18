import numpy as np

from nrgise.components.grid_builder.grid_builder_abc import GridBuilderABC


class Generator(GridBuilderABC):
    """
   Concrete implementation of a `GridBuilder` as simple Generator model. Feed in is not possible.

    Args:
        power_supply_limit: The maximum amount of power (kW) which can be supplied. This value must be positive.

    """
    def __init__(self,
                 label: str,
                 power_supply_limit: float = np.inf,
                 ):
        """
        Args:
            power_supply_limit: must be +ve value, defaults to +infinity
        """
        super().__init__(label=label, power_supply_limit=power_supply_limit, feed_in_limit=0)
