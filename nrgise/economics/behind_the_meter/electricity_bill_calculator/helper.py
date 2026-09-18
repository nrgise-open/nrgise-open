import warnings
from math import isclose

import numpy as np


def raise_if_load_profile_is_not_one_year(
    list_of_grid_power_utilization: np.ndarray,
    time_delta_seconds: int,
) -> None:
    one_year_in_seconds = 8760 * 60 * 60
    one_week_in_seconds = 7 * 24 * 60 * 60
    if not isclose(len(list_of_grid_power_utilization) * time_delta_seconds,
                   one_year_in_seconds,
                   abs_tol=one_week_in_seconds):
        warnings.warn('The `list_of_grid_power_utilization` and `time_delta_seconds` provided does not represent'
                      'one year.')
