from typing import Union

import numpy as np
import pandas as pd

from nrgise.common.state import State
from nrgise.common.types import GenericSequence
from nrgise.forecasters.forecaster_abc import ForecasterABC


class ForecastReplayForecaster(ForecasterABC):
    """
    Forecaster that replays predefined rolling-horizon forecasts.

    It returns forecasts that were computed or
    recorded in advance instead of generating them during the simulation.
    A typical use case is to run a computationally expensive forecasting model
    ahead of the simulation, store its rolling-horizon forecasts in this format,
    and replay those forecasts during one or more simulation runs.

    Forecasts are provided as a two-dimensional matrix. Each row contains the
    forecast that is available at one simulation time step, while the columns
    represent the forecast horizons `t+1`, `t+2`, `t+3`, and so on.

    Conceptually, the expected input has the following structure:

    ```
    forecast          forecast horizon
    issued at       t+1    t+2    t+3    t+4
    ------------------------------------------
    10:00          12.1   12.8   13.4   14.0
    10:15          12.5   13.1   13.8   14.2
    10:30          12.9   13.5   14.0   14.4
    10:45          13.2   13.8   14.3   14.7
    11:00          13.6   14.1   14.5   14.9
    ```

    For example, if the current simulation time corresponds to `10:15`,
    calling `predict(3)` returns:

    ```
    [12.5, 13.1, 13.8]
    ```

    These values correspond to the `t+1`, `t+2`, and `t+3` forecasts that
    were available at 10:15.

    This representation allows forecasts for the same target time to change
    depending on when they were issued. It can therefore reproduce realistic
    forecasting behavior, such as forecast errors decreasing as the target
    time approaches.


    Args:
        forecast_data: Two-dimensional array or `pandas.DataFrame` containing the forecasts
            to replay. Rows correspond to simulation time steps (forecast issue
            times), and columns correspond to forecast horizons (`t+1`, `t+2`,
            ...).
        standard_deviation: Standard deviation of zero-mean Gaussian noise added to the forecast.
        time_delta_seconds: Time interval represented by one step in `forecast_data`, in seconds.
    """

    def __init__(
            self,
            forecast_data: Union[pd.DataFrame, np.ndarray],
            standard_deviation: float = 0,
            time_delta_seconds: int = 0,
        ) -> None:
        # Working with numpy and int indexes rather with timestamp indexing for performance reasons.
        self._forecast_data = np.array(forecast_data)
        self._standard_deviation = standard_deviation
        self._time_step = 0
        self._time_delta_seconds = time_delta_seconds
        np.random.seed(0)

    @property
    def time_delta_seconds(self) -> int:
        return self._time_delta_seconds

    def predict(self, forecast_length: int) -> GenericSequence:
        """
        Return the stored forecast for the current simulation time step.

        The row corresponding to the current simulation time step is selected
        from `forecast_data`. The first `forecast_length` values of that row are
        returned, corresponding to the horizons:

        ```
        [t+1, t+2, ..., t+forecast_length]
        ```

        For example, given the row:

        ```
        t+1    t+2    t+3    t+4
        12.5   13.1   13.8   14.2
        ```

        `predict(3)` returns:

        ```
        [12.5, 13.1, 13.8]
        ```

        If `forecast_length` exceeds the number of forecast horizons available
        in the stored data, a `ValueError` is raised.

        If `standard_deviation` is non-zero, zero-mean Gaussian noise is added
        independently to each returned forecast value.

        Args:
            forecast_length: Number of values to return from precomputed forecast of that time step.
        Returns:
            Forecast sequence containing `forecast_length` values.
        """
        forecast = self._forecast_data[self._time_step]
        if len(forecast) < forecast_length:
            raise ValueError('Provided forecast length is higher as the length of the defined forecast')
        forecast = np.array(forecast[:forecast_length])

        if self._standard_deviation != 0:
            return np.random.normal(forecast, self._standard_deviation)
        return forecast

    def get_current_value(self) -> float:
        """Raise because replay data contains only future forecast horizons."""
        raise NotImplementedError(
            'ForecastReplayForecaster cannot provide a current observed value.',
        )

    def fit(self, state: State) -> None:
        """
        The fit of this forecaster can be seen as a "pseudo-fit" as we have perfect foresight.
        We just update the internal time step as pointer from where on the true forecast data should be returned.
        """
        self._time_step = state.time_step

