import numpy as np
import pandas as pd
import pytest

from nrgise import EnergySystem, Simulation
from nrgise.common.constants import SECONDS_PER_YEAR
from nrgise.components import AgingLinearCapacityWrapper, Battery, Grid, PowerProfile
from nrgise.components.storage.helper import calc_equivalent_cycle
from nrgise.controllers import SelfConsumptionController


@pytest.mark.parametrize(
    "simulation_time_days, expected", [(365 / 2, 0.9), (365, 0.8), (400, 0.8)],
)
def test_calendric_aging_only(simulation_time_days, expected):
    storage = Battery(nom_power=100, capacity=100, time_delta_seconds=3600 * 24, label='')
    aging_storage = AgingLinearCapacityWrapper(storage=storage, lifetime_in_years=1, max_cycles=100, eol=0.8)

    for _ in range(int(simulation_time_days)):
        aging_storage.set_power_contribution(0)

    state = aging_storage.get_state()
    assert aging_storage.soh == pytest.approx(expected, abs=0.01)
    assert storage.capacity == pytest.approx(aging_storage.initial_capacity * expected, abs=0.03)
    assert state['calendaric_soh_loss'] == pytest.approx(1 - expected, abs=0.01)
    assert state['cycling_soh_loss'] == pytest.approx(0, abs=0.01)


@pytest.mark.parametrize(
    "cycles, expected", [(5, 0.9), (0, 1), (10, 0.8), (20, 0.8)],
)
def test_cyclic_aging_only(cycles, expected):
    storage = Battery(nom_power=1000, capacity=1000, time_delta_seconds=3600,
                                           initial_soc=0, label='')
    aging_storage = AgingLinearCapacityWrapper(storage=storage, lifetime_in_years=np.inf, max_cycles=10, eol=0.8)

    for _ in range(int(cycles)):
        aging_storage.set_power_contribution(-1000)
        aging_storage.set_power_contribution(1000)

    state = aging_storage.get_state()
    assert aging_storage.equivalent_cycles == pytest.approx(cycles, abs=0.0001)
    assert state['calendaric_soh_loss'] == pytest.approx(0, abs=0.01)
    assert state['cycling_soh_loss'] == pytest.approx(1 - expected, abs=0.01)
    assert aging_storage.soh == pytest.approx(expected, abs=0.01)


def test_combined_aging():
    storage = Battery(nom_power=1000, capacity=1000, time_delta_seconds=int(SECONDS_PER_YEAR / 2),
                                           initial_soc=0, label='')
    aging_storage = AgingLinearCapacityWrapper(storage=storage, lifetime_in_years=10, max_cycles=10, eol=0.8)
    for _ in range(5):
        aging_storage.set_power_contribution(-1000)
        aging_storage.set_power_contribution(1000)
    state = aging_storage.get_state()
    assert state['calendaric_soh_loss'] == pytest.approx(0.1, abs=0.01)
    assert state['cycling_soh_loss'] == pytest.approx(0.1, abs=0.01)
    assert aging_storage.soh == pytest.approx(0.9, abs=0.01)


@pytest.mark.parametrize(
    "eol, equivalent_cycles, max_cycles, expected", [(0, 100, 1000, 0.1),
                                                     (0.2, 1100, 1000, 0.8),
                                                     ],
)
def test_linear_cycling_aging_based_soh_loss(eol, equivalent_cycles, max_cycles, expected):
    soh = AgingLinearCapacityWrapper.calculate_cyclic_aging_based_soh_loss(eol=eol, equivalent_cycles=equivalent_cycles,
                                                                           max_cycles=max_cycles)
    assert soh == expected


@pytest.mark.parametrize(
    "eol, age, lifetime, expected", [(0, 1, 10, 0.1),
                                     (0.2, 11, 10, 0.8),
                                     ],
)
def test_linear_calendric_aging_based_soh_loss(eol, age, lifetime, expected):
    soh = AgingLinearCapacityWrapper.calculate_calendric_aging_based_soh_loss(eol=eol, storage_age=age,
                                                                              lifetime=lifetime)
    assert soh == expected


@pytest.mark.parametrize(
    "cycling_soh_loss, aging_soh_loss, expected", [(0.1, 0, 0.9), (0.3, 0.5, 0.8)],
)
def test_linear_aging_soh(cycling_soh_loss, aging_soh_loss, expected):
    soh = AgingLinearCapacityWrapper.calculate_soh(cycling_soh_loss=cycling_soh_loss,
                                                   aging_soh_loss=aging_soh_loss,
                                                   eol=0.8)
    assert soh == expected


@pytest.mark.parametrize(
    "power, expected", [(0, 0),
                        (100, 0.5),
                        (200, 0.5),
                        ],
)
def test_calc_fec(power, expected):
    fec = calc_equivalent_cycle(power, 3600, 100)
    assert fec == expected


def test_equivalent_cycles():
    load_deload_cicles = 10
    storage = Battery(label='battery',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           initial_soc=1)
    aging_storage = AgingLinearCapacityWrapper(storage=storage, lifetime_in_years=1, max_cycles=load_deload_cicles,
                                               eol=0.7)

    for _i in range(load_deload_cicles):
        aging_storage.set_power_contribution(100)  # discharge
        aging_storage.set_power_contribution(-100)  # charge

    assert aging_storage.equivalent_cycles == load_deload_cicles


@pytest.mark.parametrize(
    "replace_storage", [True, False],
)
def test_soh_when_max_cycles_complete(replace_storage):
    max_cycles = 10
    storage = Battery(label='battery',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           initial_soc=0)
    aging_storage = AgingLinearCapacityWrapper(storage=storage, lifetime_in_years=1, max_cycles=max_cycles, eol=0.7,
                                               replace_storage_when_eol_reached=replace_storage)

    for _ in range(max_cycles):
        aging_storage.set_power_contribution(-100)  # charge
        aging_storage.set_power_contribution(100)  # discharge

    if replace_storage:
        assert aging_storage.soh == 1
    else:
        assert aging_storage.soh == 0.7


def test_battery_reset():
    storage = Battery(label='battery',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           initial_soc=0.4)
    aging_storage = AgingLinearCapacityWrapper(storage=storage, lifetime_in_years=1, max_cycles=100, eol=0.7)

    for _ in range(10):
        aging_storage.set_power_contribution(10)
        aging_storage.set_power_contribution(-10)
    aging_storage.reset()
    assert storage.soc == 0.4
    assert aging_storage.soh == 1
    assert storage.capacity == 100
    assert aging_storage.equivalent_cycles == 0


def test_wrapper_extends_state():
    storage = Battery(label='battery',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           initial_soc=0)
    aging_storage = AgingLinearCapacityWrapper(storage=storage, lifetime_in_years=1, max_cycles=100, eol=0.7)

    state = aging_storage.get_state()

    assert state['soc'] == 0
    assert state['soh'] == 1
    assert state['capacity'] == 100
    assert state['equivalent_cycles'] == 0


def test_simulation_results_with_wrapped_storage_contains_information():
    storage = Battery(label='storage', nom_power=100, capacity=100, time_delta_seconds=3600,
                                           initial_soc=0)
    aging_storage = AgingLinearCapacityWrapper(storage, lifetime_in_years=100, max_cycles=100, eol=0.7)
    es = EnergySystem(time_index=pd.date_range(start='2021-01-01 00:00', periods=10, freq='1h'))
    load = PowerProfile(label='load', power_profile=[-1 for _ in range(10)])
    pv = PowerProfile(label='pv', power_profile=[2 for _ in range(10)])
    grid = Grid(label='grid')
    es.add_components(aging_storage, load, pv, grid)
    controller = SelfConsumptionController(storage_label='storage')
    results = Simulation(es, controller).run()

    assert {'components_states.storage.soc', 'components_states.storage.soh', 'components_states.storage.capacity',
            'components_states.storage.equivalent_cycles'}.issubset(results.columns)


def test_wrapper_throws_if_wrong_storage_class_passed():
    storage = {'pretend_to_be_storage': True}
    with pytest.raises(Exception) as exception_info:
        AgingLinearCapacityWrapper(storage=storage, lifetime_in_years=1, max_cycles=100, eol=0.7)  # type: ignore
    assert exception_info.errisinstance(TypeError)
