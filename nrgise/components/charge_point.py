from typing import Any, List, Optional

import pandas as pd

from nrgise.common.helper import get_time_delta_seconds
from nrgise.components.capabilities.controllable_mixin import ControllableMixin
from nrgise.components.capabilities.data_profile_mixin import DataProfileMixin
from nrgise.components.capabilities.publishes_state_mixin import PublishesStateMixin
from nrgise.components.capabilities.time_step_aware_mixin import TimeStepAwareMixin
from nrgise.components.charge_schedule import ChargeEvent, ChargeSchedule
from nrgise.components.storage.battery import Battery


class ChargePoint(DataProfileMixin, ControllableMixin, PublishesStateMixin, TimeStepAwareMixin):
    """
    This class implements a charge point for electric vehicles.
    If an electric vehicle is connected to the charge point, it will show a
    Battery in ``self._electric_vehicle``, which can be charged and discharged.
    It uses the ``charge_schedule`` to determine when an EV is connected, and if so, with which capacity and which
    initial SOC it arrived. The ``ChargeEvent``s of the schedule are mapped onto the simulation time steps of
    ``time_index``: an EV is connected at a time step with timestamp ``t`` if ``arrival <= t < departure``. Event end
    times are handled exclusively, so an EV departing at a timestamp is not considered connected during the following
    simulation interval. Consecutive charge events without an idle time step in between are handled as separate EVs.

    Example of a charge schedule containing two electric vehicles
    (first EV is connected for 30 minutes, second EV for 15 minutes):
    ```python
    charge_schedule = ChargeSchedule()
    charge_schedule.add_charge_event(
        ChargeEvent(arrival=pd.Timestamp('2021-01-01 10:00'), departure=pd.Timestamp('2021-01-01 10:30'),
                    capacity=60, soc_arrival=0.2))
    charge_schedule.add_charge_event(
        ChargeEvent(arrival=pd.Timestamp('2021-01-01 10:45'), departure=pd.Timestamp('2021-01-01 11:00'),
                    capacity=80, soc_arrival=0.1))
    ```

    Args:
        label: The component label
        charge_schedule: The charge events at this charge point.
        time_index: The time index of the simulation (the same as passed to the ``EnergySystem``).
        ev_charge_power_limit: the charging power limit of the EV. The ev battery is assumed to be an one-hour battery
        ev_discharge_power_limit: the discharging power limit of the EV


    """
    def __init__(self,
                 label: str,
                 charge_schedule: ChargeSchedule,
                 time_index: pd.DatetimeIndex,
                 ev_charge_power_limit: float = -50,
                 ev_discharge_power_limit: float = 50) -> None:

        if ev_charge_power_limit > 0 or ev_discharge_power_limit < 0:
            raise ValueError('Make sure the passed charge limit is negative, and the discharge limit is positive.')

        self._label = label
        self._charge_events_per_time_step = charge_schedule.charge_events_per_time_step(time_index)
        self._time_delta_seconds = get_time_delta_seconds(time_index)
        self._max_charge_power = ev_charge_power_limit
        self._max_discharge_power = ev_discharge_power_limit
        self._electric_vehicle: Optional[Battery] = None
        self._connected_charge_event: Optional[ChargeEvent] = None
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

            A vehicle is connected when a charge event is active at the current
            time step which differs from the charge event of the currently
            connected vehicle. A connected vehicle is disconnected when no
            charge event is active at the current time step.
            A connected vehicle is represented by a Battery with a P/E ratio of 1.

            Args:
                time_step: Positional index of the current time step in the ``time_index``.

            Raises:
                IndexError: If ``time_step`` is outside the available data profile.
            """
        charge_event = self._charge_events_per_time_step[time_step]
        if self._electric_vehicle_needs_to_be_connected(charge_event):
            # The electric vehicle is represented by a simple battery for now.
            self._electric_vehicle = Battery(
                label='EV_arrival_time_ ' + str(time_step),
                capacity=charge_event.capacity,  # type: ignore
                nom_power=charge_event.capacity,  # type: ignore
                initial_soc=charge_event.soc_arrival,  # type: ignore
                time_delta_seconds=self._time_delta_seconds)
            self._connected_charge_event = charge_event
        if self._electric_vehicle_needs_to_be_disconnected(charge_event):
            self._electric_vehicle = None
            self._connected_charge_event = None

    def reset(self) -> None:
        """Reset the ``ChargePoint`` to its initial simulation state.

        Disconnects the currently connected EV, if any, and clears the stored
        ``time_step``. The ``charge_schedule`` and configured power limits are kept.
        """
        self._electric_vehicle = None
        self._connected_charge_event = None
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

    def _electric_vehicle_needs_to_be_connected(self, charge_event: Optional[ChargeEvent]) -> bool:
        """Return whether an EV should be connected for the charge event of the current time step.

        An EV should be connected if a charge event is active and it is not the
        charge event of the currently connected EV.
        """
        return charge_event is not None and (
            not self._electric_vehicle_connected() or charge_event != self._connected_charge_event)

    def _electric_vehicle_needs_to_be_disconnected(self, charge_event: Optional[ChargeEvent]) -> bool:
        """Return whether the connected EV should be disconnected.

            An EV should be disconnected if an EV is currently connected and no
            charge event is active at the current time step.
        """
        return self._electric_vehicle_connected() and charge_event is None

    def _electric_vehicle_connected(self) -> bool:
        "Returns: Whether an electric vehicle is currently connected"
        return self._electric_vehicle is not None

    @property
    def data_profile(self) -> List[Optional[ChargeEvent]]:
        return self._charge_events_per_time_step

    @data_profile.setter
    def data_profile(self, value: List[Optional[ChargeEvent]]) -> None:
        self._charge_events_per_time_step = list(value)

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
