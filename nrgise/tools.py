from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import pandas as pd

from nrgise.common.helper import duplicate_data, get_time_delta_seconds
from nrgise.common.types import GenericSequence
from nrgise.components.grid_builder.grid_builder_abc import GridBuilderABC

if TYPE_CHECKING:
    from nrgise.energy_system import EnergySystem

"""
This file contains convenience functions for working with nrgise, e.g. preparing input data and processing results.
"""

def stretch_data_profile(data_profile: GenericSequence,
                         date_time_index: pd.DatetimeIndex,
                         target_end_date: pd.Timestamp) -> Tuple[GenericSequence, pd.DatetimeIndex]:
    """
    Stretches a data profile by repeating until given `target_end_date`. Can be used if you only
    have a single year of data but want to simulate multiple years (e.g. to consider into aging effects of batteries).

    Args:
        data_profile: The data profile to stretch.
        date_time_index: The time index of the data profile.
        target_end_date: The end date of the stretched data profile.

    Returns:
        The stretched data profile (data only)
        The stretched time index of the data profile
    """
    start_date = date_time_index[0]

    if target_end_date < date_time_index[-1]:
        raise ValueError('`target_end_date` passed is before end of original `time_index`')
    if len(data_profile) != len(date_time_index):
        raise ValueError('`data_profile` and `date_time_index` must be the same length')

    time_delta_seconds = get_time_delta_seconds(date_time_index)
    target_date_time_index = pd.date_range(start=start_date,
                                           end=target_end_date,
                                           freq=str(int(time_delta_seconds)) + 's')

    num_of_repeats = len(target_date_time_index) / len(date_time_index)

    replicated_data = duplicate_data(data_profile, int(num_of_repeats) + 1)
    replicated_data = replicated_data[0:len(target_date_time_index)]

    return replicated_data, target_date_time_index


def get_component_powers_from_results(energy_system: EnergySystem, results: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to extract per-component power values from simulation results.

    Args:
        energy_system: Energy system the results belong to.
        results: Simulation results.

    Returns:
        filtered results only containing power values.
    """
    component_powers = pd.DataFrame()

    for component in energy_system.components:
        if component.label in energy_system.controllable_components:
            component_powers[component.label] = results['power_applied.' + component.label]
        elif component.label not in energy_system.controllable_components and not isinstance(component, GridBuilderABC):
            component_powers[component.label] = results['uncontrolled_power_contribution_per_component.' + component.label]
        elif isinstance(component, GridBuilderABC):
            component_powers[component.label] = results['grid_builder_usage']
    return component_powers

