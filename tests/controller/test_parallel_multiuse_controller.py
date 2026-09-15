import pytest

from nrgise.components import Battery
from nrgise.controllers import SelfConsumptionPeakShavingParallelController
from tests.helpers import build_test_state


@pytest.mark.parametrize(
    "residual_power_level, expected_action, expected_soc_virtual_sc_storage, "
    "expected_soc_virtual_ps_storage",
    [
        # Virtual SOCs change, even battery does not charge/discharge
        (-100, 0, 0.3, 0.7),
        # Virtual SOCs change when charging
        # -300 = -200 from self consumption - 100 from peak shaving
        (200, -300, 0.9, 0.7),
    ],
)
def test_parallel_controller_storage_always_large_enough(
        residual_power_level,
        expected_action,
        expected_soc_virtual_sc_storage,
        expected_soc_virtual_ps_storage,
):
    storage_model = Battery(
        label="storage_model",
        nom_power=1000,
        capacity=1000,
        time_delta_seconds=3600,
        initial_soc=0.5,
    )
    controller = SelfConsumptionPeakShavingParallelController(
        cut_off_power_value=-100,
        storage_model=storage_model,
        power_share_peak_shaving=0.5,
        capacity_share_peak_shaving=0.5,
        storage_label='battery',
    )

    state = build_test_state(uncontrolled_power_balance=residual_power_level)

    action, controller_state = controller.get_action(state)

    assert action == {'battery': expected_action}
    assert controller_state['virtual_self_consumption_battery_soc'] == pytest.approx(
        expected_soc_virtual_sc_storage, abs=1e-12,
    )
    assert controller_state['virtual_peak_shaving_battery_soc'] == pytest.approx(
        expected_soc_virtual_ps_storage, abs=1e-12,
    )
