import numpy as np

from nrgise.common.state import State
from nrgise.common.types import GenericSequence, UnivariateSequence
from nrgise.forecasters.forecaster_abc import ForecasterABC


class DataProfileForecaster(ForecasterABC):
    """
    Forecaster based on a predefined univariate data profile.

    It returns forecasts by looking ahead in a
    predefined sequence of values. As the simulation progresses, the current
    simulation time step is used as a moving pointer into the data profile.

    This is useful when the future profile is assumed to be known in advance,
    for example when modeling a perfect forecast or when adding a simple noise
    model to an otherwise perfect forecast.

    Returned forecasts start at the next time step (`t+1`). The current observed
    profile value is available separately through `get_current_value()`.

    If the requested forecast extends beyond the available data profile, the
    missing values are padded with zeros.

    Args:
        forecast_data: Predefined univariate data profile from which forecasts are constructed.
        standard_deviation: Standard deviation of zero-mean Gaussian noise added to the forecast.
        time_delta_seconds: Time interval represented by one step in `forecast_data`, in seconds.
    """

    def __init__(
            self,
            forecast_data: UnivariateSequence,
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
        Return a forecast of `forecast_length` values from the current simulation
        position.

        If `standard_deviation` is non-zero, zero-mean Gaussian noise is added
        independently to each returned value.

        Args:
            forecast_length: Number of values to return.

        Returns:
            Forecast sequence with exactly `forecast_length` values.
        """
        start_ts = self._time_step + 1
        forecast = self._forecast_data[start_ts: start_ts + forecast_length]
        missing_forecast_length = forecast_length - len(forecast)
        if missing_forecast_length != 0:
            forecast = np.append(forecast, np.zeros(missing_forecast_length))

        if self._standard_deviation != 0:
            return np.random.normal(forecast, self._standard_deviation)
        return forecast

    def get_current_value(self) -> float:
        """Return the profile value at the current fitted time step."""
        return float(self._forecast_data[self._time_step])

    def fit(self, state: State) -> None:
        """
        The fit of this forecaster can be seen as a "pseudo-fit" as we have perfect foresight.
        We just update the internal time step as pointer from where on the true forecast data should be returned.
        """
        self._time_step = state.time_step

