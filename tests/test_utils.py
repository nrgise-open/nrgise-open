import pandas as pd
import pytest

from nrgise import EnergySystem, Simulation
from nrgise.components import Grid, Load, Pv
from nrgise.tools import get_component_powers_from_results, stretch_data_profile


@pytest.mark.parametrize("end_timestamp, simulation_length",
                         [(pd.Timestamp("1/2/2012 23:00:00"), 48),
                          (pd.Timestamp("1/2/2012 11:00:00"), 36)])
def test_stretch_data_profile(end_timestamp, simulation_length):
    time_index = pd.date_range("1/1/2012 0:00:00", periods=24, freq="h")
    random_data_profile = pd.DataFrame({'random_data': range(24)})
    stretched_data_profile, stretched_date_time_index = stretch_data_profile(random_data_profile,
                                                                             time_index,
                                                                             end_timestamp)
    assert len(stretched_data_profile) == len(stretched_date_time_index)
    assert len(stretched_data_profile) == simulation_length
    assert stretched_date_time_index[-1] == end_timestamp


def test_get_component_powers_from_results():
    es = EnergySystem(pd.date_range("1/1/2012 0:00:00", periods=5, freq="15min"))
    load = Load(label='Load', power_profile=[-1, -2, -3, -4, -5])
    pv = Pv(label='Pv', power_profile=[5, 5, 5, 5, 5])
    grid = Grid(label='Grid')
    es.add_components(load, pv, grid)
    simulation = Simulation(es)
    results = simulation.run()
    component_powers = get_component_powers_from_results(es, results)
    assert list(component_powers['Grid']) == [-4, -3, -2, -1, 0]
