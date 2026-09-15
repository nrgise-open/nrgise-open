from abc import ABC, abstractmethod

from nrgise.common.state import State
from nrgise.common.types import GenericSequence


class ForecasterABC(ABC):
    """
    Minimal forecasting contract used by built-in NRGISE controllers.

    This interface is intentionally small and only captures the behavior required by
    forecasters currently used inside NRGISE controller implementations.

    It is **not** intended to be a universal abstraction for all forecasting workflows.
    If a forecaster or controller requires richer inputs, outputs, or interaction
    patterns, define a dedicated forecaster class and build your controller so it feeds the
    right inputs for your forecaster. However, if your own forecaster inherits this base class,
    it will work out-of-the-box with the built in nrgise controllers.

    Implementations are responsible for extracting relevant features from `State`
    in `fit`.
    """

    @property
    @abstractmethod
    def time_delta_seconds(self) -> int:
        """
        Specifies the length of a time step in seconds.

        Returns:
            The time step length in seconds.
        """
        pass

    @abstractmethod
    def predict(self, forecast_length: int) -> GenericSequence:
        """
        Creates a prediction of length `forecast_length`.
        By convention, forecasts in NRGISE start at the next time step
        (`t+1`) and therefore do not include a value for the current time step (`t0`).

        Args:
            forecast_length: How many time steps to forecast. Each time step has a length of `time_delta_seconds`.

        Returns:
            The forecast of length `forecast_length`.
        """
        pass

    @abstractmethod
    def get_current_value(self) -> float:
        """
        Return the observed value at the current fitted time step (`t0`). If not possible with impelemting forecast
        method, create a Component and pass the current observation to the *Controller* through the `State`.

        Returns:
            The current observed value.

        Raises:
            NotImplementedError: If the forecaster has no current observation.
        """
        pass

    @abstractmethod
    def fit(self, state: State) -> None:
        """
        Fits/updates the model based on the current system state.

        This method exists to support built-in NRGISE controllers that operate on
        `State`. Custom forecaster-controller pairs may choose a different input
        contract and do not need to implement `ForecasterABC`.

        Implementations are responsible for extracting relevant features from `State`.

        Args:
            state: `State` object containing the current state of the energy system.
        """
        pass
