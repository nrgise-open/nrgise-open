"""
for collection types, there is an article which describes the dependency between different types:
https://docs.python.org/3.9/library/collections.abc.html
"""

from typing import Dict, Sequence, TypeVar, Union

import numpy as np
import pandas as pd

GenericSequence = Union[
    pd.DataFrame, pd.Series, Sequence, np.ndarray]  # anything that allows to write for x in z or np.array(x)
UnivariateSequence = Union[pd.Series, Sequence, np.ndarray]
GenericMath = TypeVar("GenericMath", float, np.ndarray, pd.Series)  # all data that allows e.g. to write x = x / 100
MathSequence = TypeVar("MathSequence", np.ndarray, pd.Series)

ControlAction = Dict[str, float]

# Technically a `TimeSeries` must have a `pd.DateTimeIndex` which makes them a time series.
TimeSeries = TypeVar("TimeSeries", pd.DataFrame, pd.Series)


def is_time_series(data: TimeSeries) -> bool:
    """
    Check if the input pandas Series or DataFrame is a time series.

    Returns:
        True if the index is a DatetimeIndex, False otherwise.
    """
    if isinstance(data, (pd.Series, pd.DataFrame)):  # noqa
        if isinstance(data.index, pd.DatetimeIndex):
            return True
    return False
