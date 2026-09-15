import warnings

import numpy as np
import pandas as pd
import pytest

from nrgise.components import (
    Generator,
    Grid,
    Load,
    PowerProfile,
    Pv,
    PvCurtailable,
)


@pytest.mark.parametrize("component_class", [Pv, PowerProfile, Load])
@pytest.mark.parametrize("power_profile, expected",
                         [
                             ([1, 2, 3], [1, 2, 3]),
                         ],
                         )
def test_power_profile_component_returns_power_values(component_class, power_profile, expected):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        component = component_class(label='', power_profile=power_profile)
        for time_step in range(len(power_profile)):
            component.handle_time_step_update(time_step)
            power_contribution = component.uncontrolled_power_contribution()
            assert power_contribution == expected[time_step]


@pytest.mark.parametrize("component_class", [Pv, PowerProfile, Load])
def test_power_profile_component_reset(component_class):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        power_profile_component = component_class(label='', power_profile=[1, 2, 3])
        power_profile_component.reset()
        assert power_profile_component.uncontrolled_power_contribution() == 1


def test_pv_system_warns_when_negative_power_contribution():
    with warnings.catch_warnings(record=True) as w:
        Pv(label='', power_profile=[-1, -10])
        assert len(w) == 1


def test_load_warns_when_positive_power_contribution():
    with warnings.catch_warnings(record=True) as w:
        Load(label='', power_profile=[1, 10])
        assert len(w) == 1


def test_generator_fail_on_feed_in():
    # Test is checking if generator will accept -ve power value, which indicates a feed-in to the generator
    generator = Generator(label='', power_supply_limit=100)
    with pytest.raises(Exception) as exception_info:
        generator.supply_power(-10)
    assert exception_info.errisinstance(ValueError)


def test_grid_capacity_limits():
    grid = Grid(label='', power_supply_limit=100, feed_in_limit=-100)
    with pytest.raises(Exception) as exception_info:
        grid.supply_power(-120)
    assert exception_info.errisinstance(ValueError)
    with pytest.raises(Exception) as exception_info:
        grid.supply_power(120)
    assert exception_info.errisinstance(ValueError)

def test_controllable_pv_component():
    pv = PvCurtailable(label='pv', power_profile=np.array([100, 100, 100]))
    assert pv.set_power_contribution(200) == 100
    assert pv.set_power_contribution(-100) == 0
    assert pv.set_power_contribution(50) == 50


def test_wrong_grid_generator_supply_feed_polarity():
    # Positive feed in
    with pytest.raises(Exception) as exception_info:
        Grid(label='', power_supply_limit=10, feed_in_limit=10)
    assert exception_info.errisinstance(ValueError)
    # Negative `power_supply_limit`
    with pytest.raises(Exception) as exception_info:
        Grid(label='', power_supply_limit=-10, feed_in_limit=-10)
    assert exception_info.errisinstance(ValueError)


def test_power_profile_component_fails_when_passing_data_frame():
    datetime_index = pd.date_range(start='2019-01-01 00:00:00', end='2019-01-31 23:45:00', freq='15min')
    data_profile = pd.DataFrame(index=datetime_index, data={'load': 11})
    with pytest.raises(Exception) as exception_info:
        PowerProfile(label='data', power_profile=data_profile)  # type: ignore
    assert exception_info.errisinstance(TypeError)
