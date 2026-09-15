from typing import List

import numpy as np
import pandas as pd

from nrgise.common.types import GenericMath, GenericSequence


def convert_power_to_energy(power: GenericMath, time_delta_seconds: int) -> GenericMath:
    return power * time_delta_seconds / 3600


def convert_energy_to_power(energy: GenericMath, time_delta_seconds: int) -> GenericMath:
    return energy * 3600 / time_delta_seconds


def calculate_simulation_length_in_hours(time_index: pd.DatetimeIndex) -> float:
    return (time_index[-1] - time_index[0]).total_seconds() / 60 / 60


def get_time_delta_seconds(date_time_index: pd.DatetimeIndex) -> int:
    if date_time_index.freq is not None:
        return pd.to_timedelta(date_time_index.freq).seconds  # type: ignore
    if len(date_time_index) >= 2:
        return int((date_time_index[1] - date_time_index[0]).total_seconds())
    raise ValueError("DatetimeIndex needs a `freq` attribute or length >=2 to calculate time_delta.")


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    Flatten a hierarchical dictionary using a recursive approach.

    Args:
        d: The dictionary to be flattened.
        parent_key: The key value of the parent in string format
        sep: The separator to be used between the parent and child keys.
    Returns:
        dict: The flattened dictionary.
    """
    flattened = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            flattened.update(flatten_dict(v, new_key, sep=sep))
        else:
            flattened[new_key] = v
    return flattened


def duplicate_data(data: GenericSequence, num_duplicates: int) -> GenericSequence:
    if isinstance(data, (pd.DataFrame, pd.Series)):
        return pd.concat([data] * num_duplicates, ignore_index=True)  # type: ignore
    if isinstance(data, List):
        return data * num_duplicates
    if isinstance(data, np.ndarray):
        return np.tile(data, num_duplicates)
    raise TypeError("Unsupported data type")
