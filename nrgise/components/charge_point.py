import math
from typing import Any, Optional

import pandas as pd

from nrgise.components.capabilities.controllable_mixin import ControllableMixin
from nrgise.components.capabilities.data_profile_mixin import DataProfileMixin
from nrgise.components.capabilities.publishes_state_mixin import PublishesStateMixin
from nrgise.components.capabilities.time_step_aware_mixin import TimeStepAwareMixin
from nrgise.components.storage.battery import Battery


class ChargePoint(DataProfileMixin, ControllableMixin, PublishesStateMixin, TimeStepAwareMixin):
    """
    This class implements a charge point for electric vehicles.
    If an electric vehicle is connected to the charge point, it will show a
    Battery in ``self._electric_vehicle``, which can be charged and discharged.
    It uses the ``charge_event_data`` as a data profile of when an EV is
    connected, and if so, with which capacity and which initial SOC it arrived.
    A non-null ``soc_arrival`` indicates that an EV is connected. Event end times are handled exclusively,
    so an EV departing at a timestamp is not considered connected during the following simulation interval.

    Example structure of charge_event_data containing two electric vehicles
    (first EV is connected for 30 minutes, second EV for 15 minutes):
    ```
    time_stamp     soc_arrival  capacity
    ------------------------------------------
    09:45          nan          nan
    10:00          0.2          60
    10:15          0.2          60
    10:30          nan          nan
    10:45          0.1          80
    11:00          nan          nan
    ```

    Args:
        label: The component label
        charge_event_data: The charge event data contains the timestamps as
            index, and columns soc_arrival, capacity (nan if no car is
            present).
            It has one entry per simulation time step.
        time_delta_seconds: The resolution of the simulation
        ev_charge_power_limit: the charging power limit of the EV. The ev battery is assumed to be an one-hour battery
        ev_discharge_power_limit: the discharging power limit of the EV


    """
    def __init__(self,
                 label: str,
                 charge_event_data: pd.DataFrame,
                 time_delta_seconds: int,
                 ev_charge_power_limit: float = -50,
                 ev_discharge_power_limit: float = 50) -> None:

        if ev_charge_power_limit > 0 or ev_discharge_power_limit < 0:
            raise ValueError('Make sure the passed charge limit is negative, and the discharge limit is positive.')

        self._label = label
        self._charge_event_data = charge_event_data
        self._time_delta_seconds = time_delta_seconds
        self._max_charge_power = ev_charge_power_limit
        self._max_discharge_power = ev_discharge_power_limit
        self._electric_vehicle: Optional[Battery] = None
        self._time_step = None

    def get_state(self) -> dict[str, Any]:
        """Return the current connection state and properties of the EV.

        Returns:
            A dictionary containing the following keys:

                - ``ev_connected``: Whether an electric vehicle is connected.
                - ``ev_soc``: The connected EV's state of charge, or ``None`` if no
                EV is connected.
                - ``ev_capacity``: The connected EV's battery capacity, or ``None``
                if no EV is connected.
        """
        if self._electric_vehicle_connected():
            # data_profile is always a pd.Dataframe, that is why types are ignored
            return {
                'ev_connected': True,
                'ev_soc': self._electric_vehicle.soc,  # type: ignore
                'ev_capacity': self._electric_vehicle.capacity,  # type: ignore
            }
        return {
            'ev_connected': False,
            'ev_soc': None,
            'ev_capacity': None,
        }

    def handle_time_step_update(self, time_step: int) -> None:
        """Updates the EV connection state for the given simulation time step.

            A vehicle is connected when ``soc_arrival`` contains a value at the
            current time step. A connected vehicle is disconnected when
            ``soc_arrival`` is ``NaN``.
            A connected vehicle is represented by a Battery with a P/E ratio of 1.

            Args:
                time_step: Positional index of the current time step in the ``charge_event_data`` profile.

            Raises:
                IndexError: If ``time_step`` is outside the available data profile.
            """
        if self._electric_vehicle_needs_to_be_connected(time_step):
            # The electric vehicle is represented by a simple battery for now.
            self._electric_vehicle = Battery(
                # data_profile is always a pd.Dataframe, that is why types are ignored
                label='EV_arrival_time_ ' + str(time_step),
                capacity=self.data_profile.iloc[time_step]['capacity'],  # type: ignore
                nom_power=self.data_profile.iloc[time_step]['capacity'],  # type: ignore
                initial_soc=self.data_profile.iloc[time_step]['soc_arrival'],  # type: ignore
                time_delta_seconds=self._time_delta_seconds)
        if self._electric_vehicle_needs_to_be_disconnected(time_step):
            self._electric_vehicle = None

    def reset(self) -> None:
        """Reset the ``ChargePoint`` to its initial simulation state.

        Disconnects the currently connected EV, if any, and clears the stored
        ``time_step``. The ``charge_event_data`` and configured power limits are kept.
        """
        self._electric_vehicle = None
        self._time_step = None

    def set_power_contribution(self, power: float) -> float:
        """Set the requested power contribution of the connected EV.

        Negative power values represent EV charging, while positive values
        represent EV discharging. The requested power is limited to the
        configured charging and discharging bounds before it is forwarded to
        the EV battery.

        Args:
            power: Requested power contribution.

        Returns:
            The actual power contribution accepted by the EV battery, or ``0``
            if no EV is connected.
        """
        if self._electric_vehicle_connected():
            charge_power = _enforce_charge_limits(power, self._max_discharge_power, self._max_charge_power)
            # data_profile is always a pd.Dataframe, that is why types are ignored
            return self._electric_vehicle.set_power_contribution(charge_power)  # type: ignore
        return 0

    def _electric_vehicle_needs_to_be_connected(self, time_step: int) -> bool:
        """Return whether an EV should be connected at the given time step.

        An EV should be connected if no EV is currently connected and the
        ``soc_arrival`` value at the current time step is not ``NaN``.
        """
        return not self._electric_vehicle_connected() and not math.isnan(
            self.data_profile.iloc[time_step]['soc_arrival'])  # type: ignore

    def _electric_vehicle_needs_to_be_disconnected(self, time_step: int) -> bool:
        """Return whether the connected EV should be disconnected.

            An EV should be disconnected if an EV is currently connected and the
            ``soc_arrival`` value at the current time step is ``NaN``.
        """
        return (self._electric_vehicle_connected() and
                math.isnan(self.data_profile.iloc[time_step]['soc_arrival']))  # type: ignore

    def _electric_vehicle_connected(self) -> bool:
        "Returns: Whether an electric vehicle is currently connected"
        return self._electric_vehicle is not None

    @property
    def data_profile(self) -> pd.DataFrame:
        return self._charge_event_data

    @data_profile.setter
    def data_profile(self, value: pd.DataFrame) -> None:
        self._charge_event_data = pd.DataFrame(value)

    @property
    def label(self) -> str:
        return self._label

    @property
    def electric_vehicle(self) -> Optional[Battery]:
        return self._electric_vehicle

    @electric_vehicle.setter
    def electric_vehicle(self, value: Optional[Battery]) -> None:
        self._electric_vehicle = value

def _enforce_charge_limits(power: float, max_discharge_power: float, max_charge_power: float) -> float:
    """Limit a power request to the configured charging bounds."""
    return min(power, max_discharge_power) if power > 0 else max(power, max_charge_power)
