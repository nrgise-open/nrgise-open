from nrgise.components.component_abc import ComponentABC


class GridBuilderABC(ComponentABC):
    """
    Base class for grid builders.

    An `EnergySystem` needs one grid builder to supply power to the system and
    accept feed-in power from the system.

    Note that requesting positive power means there is a deficit of power in
    the energy system and power needs to be provided by the grid builder.
    Requesting negative power means there is a surplus of power in the energy
    system and the grid builder needs to accept feed-in power.

    Args:
        power_supply_limit: The maximum amount of power (kW) which can be supplied. This value must be positive.
        feed_in_limit: The maximum amount of power (kW) which can be accepted as feed-in. This value must be negative.
    """

    def __init__(
            self,
            label: str,
            power_supply_limit: float,
            feed_in_limit: float,
        ) -> None:

        self._label = label
        if feed_in_limit > 0:
            raise ValueError('Feed in cannot be positive.')
        if power_supply_limit < 0:
            raise ValueError('Power supply cannot be negative.')
        self._power_supply_limit = power_supply_limit
        self._feed_in_limit = feed_in_limit

    def supply_power(self, requested_power: float) -> float:
        """
        Called by the `Simulation` at the end of each time step to level the
        energy balance of the enrgy system.
        Note that requesting positive power means there is a deficit of power
        in the energy system and power needs to be provided by the grid builder.
        Requesting negative power means there is a surplus of power in the
        energy system and the grid builder needs to accept feed-in power.

        Args:
            requested_power: The power (kW) which is requested by the energy system.

        Returns:
            The power which was requested. If it does not match with the
                requested power, the energy system is not balanced and an error is
                raised in the `Simulation`.
        """
        if requested_power > self._power_supply_limit:
            raise ValueError('Can not deliver sufficient power in order to balance the energy system. '
                             'Make sure power_supply_limit is positive.')
        if requested_power < self._feed_in_limit:
            raise ValueError('Can not accept feed in power, over feed-in capacity limit. '
                             'Make sure feed_in_limit is negative.')
        return requested_power

    def reset(self) -> None:
        pass

    @property
    def label(self) -> str:
        return self._label
