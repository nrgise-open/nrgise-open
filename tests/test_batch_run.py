from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from nrgise import BatchRun, Simulation
from nrgise.common.constants import HOURS_PER_YEAR
from nrgise.controllers import SelfConsumptionController
from tests.helpers import build_energy_system_with_battery, build_profile_data


class MyBatchRun(BatchRun):
    def __init__(self,
                 result_directory_name,
                 load_profile,
                 pv_generation_profile,
                 parameter_space,
                 date_time_index,
                 baseline_results):
        self.load_profile = load_profile
        self.pv_generation_profile = pv_generation_profile
        self.date_time_index = date_time_index
        self.baseline_results = baseline_results
        super().__init__(parameter_space=parameter_space, result_directory_name=result_directory_name)

    def perform_single_simulation(self, parameters):  # SimulationResults, Summary
        data = build_profile_data(self.load_profile, self.pv_generation_profile, self.date_time_index)
        energy_system = build_energy_system_with_battery(
            data,
            battery_capacity=parameters['capacity'],
            battery_power=parameters['power'],
        )

        simulation = Simulation(
            controller=SelfConsumptionController(storage_label='battery'), energy_system=energy_system)
        single_run_trajectory = simulation.run()

        summary = {
            'parameters': parameters,
        }

        return single_run_trajectory, summary


def test_batch_run_writes_results_for_all_parameter_combinations():
    parameter_space = {
        'capacity': [1, 2],
        'power': [1, 2],
    }

    with TemporaryDirectory() as result_directory:
        batch_run = MyBatchRun(
            result_directory_name=result_directory,
            parameter_space=parameter_space,
            load_profile=[-1 for _ in range(HOURS_PER_YEAR)],
            pv_generation_profile=[1 for _ in range(HOURS_PER_YEAR)],
            date_time_index=pd.date_range(start='2021-01-01 00:00', periods=HOURS_PER_YEAR, freq='1h'),
            baseline_results=None)
        batch_run.run()

        result_path = Path(result_directory)
        summary_path = result_path / 'batch_run_summary.csv'
        requirements_path = result_path / 'requirements.txt'
        trajectory_paths = sorted((result_path / 'trajectories').glob('*.csv'))

        assert summary_path.is_file()
        assert requirements_path.is_file()
        assert requirements_path.stat().st_size > 0
        assert [path.name for path in trajectory_paths] == ['0.csv', '1.csv', '2.csv', '3.csv']

        summary = pd.read_csv(summary_path)
        expected_summary = pd.DataFrame({
            'run_id': [0, 1, 2, 3],
            'parameters.capacity': [1, 1, 2, 2],
            'parameters.power': [1, 2, 1, 2],
        })
        pd.testing.assert_frame_equal(summary, expected_summary)

        for trajectory_path in trajectory_paths:
            assert len(pd.read_csv(trajectory_path)) == HOURS_PER_YEAR
