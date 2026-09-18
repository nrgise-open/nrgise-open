from typing import Any

from nrgise.common.state import State
from nrgise.controllers.controller_abc import ControllerABC


class FastChargePointController(ControllerABC):
    """
    A Controller for fast charging. The controller coordinates the amount of
    power which is used from a stationary storage which enables fast charging
    an electric vehicle. If the soc of the stationary storage is not
    sufficient, "slower" charging is done by using power from the grid. If no
    electric vehicle is connected, the stationay storage is charged.

    Args:
        charge_point_label: Used to wire charge point and its connected
            stationary storage together
        stationary_storage_label: Used to wire charge point and its connected stationary
            storage together
        fast_charge_soc_limit: If the batteries soc is greater than
            ``fast_charge_soc_limit`` fast charging can be done.
        fast_charge_power: Amount of power used to fast charge from the
            stationary storage. Usually the power which can be served by the
            storage.
        slow_charge_power: Amount of power used to slow charge from the grid
            connection point. Usually the power which can be provided by the
            grid.
        stationary_storage_charging_power: How much power to use to charge the battery if
            no car is connected to the charge point.
    """

    def __init__(self,
                 charge_point_label: str,
                 stationary_storage_label: str,
                 fast_charge_soc_limit: float = 0.3,
                 fast_charge_power: float = 50,
                 slow_charge_power: float = 10,
                 stationary_storage_charging_power: float = 10,
                 ):
        self._charge_point_label = charge_point_label
        self._storage_label = stationary_storage_label
        self._fast_charge_soc_limit = fast_charge_soc_limit
        self._fast_charge_power = fast_charge_power
        self._slow_charge_power = slow_charge_power
        self._battery_charging_power = stationary_storage_charging_power

    def get_action(self, state: State) -> tuple[dict[str, float], Any]:
        """Determine charging power setpoints for the charge point and stationary storage.

        If an electric vehicle is connected and the stationary storage state of
        charge (SoC) exceeds the ``fast_charge_soc_limit``, the vehicle is
        charged using the stationary storage at ``fast_charge_power``. Otherwise, the vehicle is
        charged from the grid at ``slow_charge_power``.

        If no vehicle is connected, the stationary storage is charged using the
        configured ``_battery_charging_power``.

        Args:
            state: Current system state. It must include an ``ev_connected`` value
                for the configured charge point and an ``soc`` value for the
                configured stationary storage:
                ```
                {'<charge_point_label>': {'ev_connected': bool},
                 '<stationary_storage_label>': {'soc': float}}
                ```
                Using the Battery and ChargePoint components will ensure that these values are present in the state.

        Returns:
            A tuple containing a dictionary with requested powers for charge
                point and stationary battery, indexed by their labels. For both
                components: negative power values represent battery charging, while
                positive power values represent battery discharging; and ``None``,
                because this controller does not maintain controller state.
        """
        # Check if car is connected
        if state.components_states[self._charge_point_label]['ev_connected']:
            # Check if stationary battery is charged enough in order to provide fast charging
            if state.components_states[self._storage_label]['soc'] > self._fast_charge_soc_limit:
                # Use power from the stationary battery to fast charge the car
                electric_vehicle_charge_power = -self._fast_charge_power
                battery_power = self._fast_charge_power
            else:
                electric_vehicle_charge_power = -self._slow_charge_power
                battery_power = 0
        else:
            # Charge the stationary battery if no electric vehicle is connected
            electric_vehicle_charge_power = 0
            battery_power = -self._battery_charging_power

        controller_state = None

        return {self._charge_point_label: electric_vehicle_charge_power,
                self._storage_label: battery_power}, controller_state
