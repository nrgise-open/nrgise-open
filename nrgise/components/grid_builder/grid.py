
import numpy as np

from nrgise.components.grid_builder.grid_builder_abc import GridBuilderABC


class Grid(GridBuilderABC):
    """
   Concrete implementation of a `GridBuilder` as simple Grid model.
    Args:
        power_supply_limit: The maximum amount of power (kW) which can be supplied. This value must be positive.
        feed_in_limit: The maximum amount of power (kW) which can be accepted as feed-in. This value must be negative.

    """
    def __init__(
            self,
            label: str,
            power_supply_limit: float = np.inf,
            feed_in_limit: float = -np.inf,
    ):
        super().__init__(label=label, power_supply_limit=power_supply_limit, feed_in_limit=feed_in_limit)
