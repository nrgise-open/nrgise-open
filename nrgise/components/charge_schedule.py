from dataclasses import dataclass
from typing import List, Optional

import pandas as pd


@dataclass(frozen=True)
class ChargeEvent:
    """
    A single charge event, i.e. the time period in which an electric vehicle is connected to a charge point.

    The event end time is handled exclusively: an EV departing at a timestamp is not considered connected during the
    simulation interval starting at that timestamp.

    Args:
        arrival: Time at which the EV is connected to the charge point.
        departure: Time at which the EV is disconnected from the charge point.
        capacity: Battery capacity of the EV in kWh.
        soc_arrival: State of charge of the EV at arrival.
    """
    arrival: pd.Timestamp
    departure: pd.Timestamp
    capacity: float
    soc_arrival: float


class ChargeSchedule:
    """
    The ``ChargeEvent``s of a single charge point.

    Consecutive charge events may directly follow each other (the departure of one event equals the arrival of the next
    one).

    Example:
        ```python
        schedule = ChargeSchedule()
        schedule.add_charge_event(
            ChargeEvent(arrival=pd.Timestamp('2021-01-01 10:00'), departure=pd.Timestamp('2021-01-01 10:30'),
                        capacity=60, soc_arrival=0.2))
        schedule.add_charge_event(
            ChargeEvent(arrival=pd.Timestamp('2021-01-01 10:30'), departure=pd.Timestamp('2021-01-01 10:45'),
                        capacity=80, soc_arrival=0.1))
        ```
    """

    def __init__(self) -> None:
        self._charge_events: List[ChargeEvent] = []

    def add_charge_event(self, charge_event: ChargeEvent) -> None:
        """
        Adds a charge event to the schedule.

        Args:
            charge_event: The charge event to add.

        Raises:
            ValueError: If the charge event overlaps with a charge event already in the schedule.
        """
        for existing_event in self._charge_events:
            if charge_event.arrival < existing_event.departure and existing_event.arrival < charge_event.departure:
                raise ValueError(f'{charge_event} overlaps with {existing_event}. Only one EV can be connected to a '
                                 f'charge point at a time.')
        self._charge_events.append(charge_event)

    def charge_events_per_time_step(self, time_index: pd.DatetimeIndex) -> List[Optional[ChargeEvent]]:
        """
        Maps the charge events onto the time steps of ``time_index``.

        A time step with timestamp ``t`` belongs to a charge event if ``arrival <= t < departure``. Charge events which
        do not contain any timestamp of ``time_index`` are therefore not part of the result.

        Args:
            time_index: The time index of the simulation.

        Returns:
            One entry per time step: the charge event active at that time step, or ``None`` if no EV is connected.
        """
        charge_events_per_time_step: List[Optional[ChargeEvent]] = [None] * len(time_index)
        for charge_event in self._charge_events:
            start = int(time_index.searchsorted(charge_event.arrival, side='left'))
            end = int(time_index.searchsorted(charge_event.departure, side='left'))
            charge_events_per_time_step[start:end] = [charge_event] * (end - start)
        return charge_events_per_time_step
