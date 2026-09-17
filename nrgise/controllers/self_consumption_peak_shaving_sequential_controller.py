from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np

from nrgise.common.state import State
from nrgise.controllers.controller_abc import ControllerABC
from nrgise.controllers.peak_shaving_controller import PeakShavingController
from nrgise.controllers.self_consumption_controller import SelfConsumptionController
from nrgise.forecasters.forecaster_abc import ForecasterABC


class SelfConsumptionPeakShavingSequentialController(ControllerABC):
    """
    Controller which switches between `SelfConsumptionController` and `PeakShavingController`
    (the "switching" makes it sequential). Key
    assumption is that we are using peak shaving if we see any peak in the
    forecast or in the current time step. If not, we are doing
    self consumption.

    More details can be found here: https://doi.org/10.1016/j.apenergy.2025.125353

    Args:
        load_forecaster: Forecaster for the load.
        pv_generation_forecaster: Forecaster for renewable generation (e.g. PV).
        storage_label: Label of the storage to be controlled.
        forecast_length: Length (number of time steps) of the forecast
            retrieved from the forecaster. If any peak is present in the forecast we are
            doing peak shaving.
        peak_shaving_cut_off_power_value: The *maximum* power value which
            should be reached by using peak shaving. See `PeakShavingController`
            controller for more details.
    """

    def __init__(
            self,
            load_forecaster: ForecasterABC,
            pv_generation_forecaster: ForecasterABC,
            storage_label: str,
            peak_shaving_cut_off_power_value: float,
            forecast_length: int = 12,
    ) -> None:
        self._storage_label = storage_label
        self._load_forecaster = load_forecaster
        self._pv_generation_forecaster = pv_generation_forecaster
        self._peak_shaving_controller = PeakShavingController(
            peak_shaving_cut_off_power_value, storage_label=storage_label)
        self._self_consumption_maximization_controller = SelfConsumptionController(storage_label=storage_label)
        self._forecast_length = forecast_length
        self._active_controller: Optional[ControllerABC] = None

    def get_action(self, state: State) -> Tuple[Dict[str, float], Any]:
        self._load_forecaster.fit(state)
        load_forecast = np.array(self._load_forecaster.predict(self._forecast_length))
        self._pv_generation_forecaster.fit(state)
        pv_forecast = np.array(self._pv_generation_forecaster.predict(self._forecast_length))
        residual_generation_forecast = load_forecast + pv_forecast

        if self._forecasted_power_exceeds_cutoff_value(residual_generation_forecast,
                                                       self._peak_shaving_controller._cut_off_power_value):
            self._active_controller = self._peak_shaving_controller
        elif state.uncontrolled_power_balance < self._peak_shaving_controller._cut_off_power_value:
            # Handle Case if peak is present now !
            self._active_controller = self._peak_shaving_controller
        else:
            self._active_controller = self._self_consumption_maximization_controller

        controller_state: Dict[str, Any] = {'load_forecast': list(load_forecast), 'pv_forecast': list(pv_forecast),
                            'active_controller': type(self._active_controller)}

        action, _ = self._active_controller.get_action(state)

        return action, controller_state

    @staticmethod
    def _forecasted_power_exceeds_cutoff_value(residual_generation_forecast: Iterable[float],
                                               cut_off_power_value: float) -> bool:
        """check if the residual load forecast exceeds the cutoff value at any point in time"""
        residual_generation_forecast = np.array(residual_generation_forecast)
        if len(residual_generation_forecast) == 0:
            return False
        return np.any(residual_generation_forecast < cut_off_power_value)  # type: ignore
