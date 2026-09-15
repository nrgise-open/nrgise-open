## Forecasting

Forecasts returned by `predict()` begin at the next time step (`t+1`). A
forecaster can expose the observation at the fitted current time step (`t0`)
separately through `get_current_value()`. Forecasters without a current
observation raise `NotImplementedError` from that method.

::: nrgise.forecasters.ForecasterABC

----------------------

::: nrgise.forecasters.DataProfileForecaster

----------------------

::: nrgise.forecasters.ForecastReplayForecaster
