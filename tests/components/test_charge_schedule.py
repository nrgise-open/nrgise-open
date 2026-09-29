import pandas as pd
import pytest

from nrgise.components import ChargeEvent
from tests.helpers import build_charge_event, build_charge_schedule


@pytest.mark.parametrize(
    "start_step, end_step",
    [(1, 3), (0, 2), (2, 4), (0, 4)],
)
def test_charge_schedule_raises_for_overlapping_charge_events(start_step, end_step):
    charge_schedule = build_charge_schedule(build_charge_event(1, 3))
    with pytest.raises(ValueError):
        charge_schedule.add_charge_event(build_charge_event(start_step, end_step))


def test_charge_events_per_time_step_with_consecutive_charge_events():
    first_event = build_charge_event(0, 2)
    second_event = build_charge_event(2, 3)
    charge_schedule = build_charge_schedule(first_event, second_event)
    time_index = pd.date_range('2012-01-01', periods=4, freq='h')
    assert charge_schedule.charge_events_per_time_step(time_index) == [first_event, first_event, second_event, None]


def test_charge_events_per_time_step_maps_arrival_between_time_steps_to_next_time_step():
    charge_event = ChargeEvent(arrival=pd.Timestamp('2021-01-01 00:10'), departure=pd.Timestamp('2021-01-01 00:45'),
                               capacity=60, soc_arrival=0.3)
    time_index = pd.date_range('2021-01-01 00:00', periods=4, freq='15min')
    assert build_charge_schedule(charge_event).charge_events_per_time_step(time_index) == [None, charge_event,
                                                                                           charge_event, None]


def test_charge_events_per_time_step_ignores_charge_events_outside_time_index():
    charge_schedule = build_charge_schedule(build_charge_event(-3, -1), build_charge_event(10, 12))
    time_index = pd.date_range('2012-01-01', periods=4, freq='h')
    assert charge_schedule.charge_events_per_time_step(time_index) == [None] * 4
