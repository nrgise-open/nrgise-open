import pytest

from nrgise.components import Battery


def test_soc_change():
    battery = Battery(label='battery',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           efficiency_charge=0.9,
                                           initial_soc=0,
    )
    battery.set_power_contribution(-50)
    assert battery.soc == pytest.approx(0.5 * 0.9, abs=1e-12)


def test_power_does_not_fit_into_storage():
    eta_charge_rate = 0.9
    battery = Battery(label='battery',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           efficiency_charge=eta_charge_rate,
                                           initial_soc=0.9,
    )
    power = battery.set_power_contribution(-50)
    assert battery.soc == 1
    assert power * eta_charge_rate == pytest.approx(-10, abs=0.001)


def test_battery_almost_empty():
    eta_discharge_rate = 0.9
    battery = Battery(label='battery',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           efficiency_discharge=eta_discharge_rate,
                                           initial_soc=0.1,
    )
    power = battery.set_power_contribution(50)
    assert battery.soc == 0
    assert power == pytest.approx(9, abs=1e-12)


def test_battery_reset():
    battery = Battery(label='battery',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           initial_soc=0.4,
                                           )
    for _i in range(10):
        battery.set_power_contribution(10)
        battery.set_power_contribution(-10)
    battery.reset()
    assert battery.soc == 0.4
