import pytest

from nrgise.controllers import TimeOfUseMPCController
from nrgise.forecasters import DataProfileForecaster
from tests.helpers import build_test_state


def build_pyomo_mpc_time_of_use_controller(time_delta_seconds, load_data, price_data):
    load_forecaster = DataProfileForecaster(load_data)
    price_forecaster = DataProfileForecaster(price_data)

    return TimeOfUseMPCController(
        load_forecaster=load_forecaster,
        price_forecaster=price_forecaster,
        storage_model_power=10,
        storage_model_capacity=10,
        forecast_length=1,
        time_delta_seconds=time_delta_seconds,
        storage_label='battery',
    )


@pytest.mark.parametrize(
    "soc, price_data, expected", [(0.5, [-1, 0], -5),
                                  (1, [-1, 0 ], 0),
                                  (1, [1, 0], 10)],
)
def test_maximum_charging_when_price_negative(soc, price_data, expected):
    load_data = [0, 0]
    controller = build_pyomo_mpc_time_of_use_controller(time_delta_seconds=3600,
                                                        load_data=load_data,
                                                        price_data=price_data)
    state = build_test_state(components_states={'battery': {'soc': soc}})

    action = controller.get_action(state)
    assert action[0]['battery'] == pytest.approx(expected, abs=0.001)
