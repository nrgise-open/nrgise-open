import itertools
import os
import time
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, as_completed
from importlib.metadata import distributions
from typing import Any, Optional, Tuple

import pandas as pd
from tqdm import tqdm

from nrgise.common.helper import flatten_dict


def get_environment_dependencies() -> pd.DataFrame:
    """Return the installed environment dependencies and their versions."""
    data = [
        {
            "package": distribution.metadata["Name"],
            "version": distribution.version,
        }
        for distribution in distributions()
    ]
    return pd.DataFrame(data).sort_values(by="package").reset_index(drop=True)


def _write_environment_dependencies_as_txt(dependency_df: pd.DataFrame, file_path: str) -> None:
    """Write environment dependencies to a requirements text file."""
    with open(file_path, "w") as file:
        for _, dependency in dependency_df.iterrows():
            file.write(f"{dependency['package']}=={dependency['version']}\n")


class BatchRun(ABC):
    """
    A `BatchRun` can be used in order to simulate multiple configurations of
    an EnergySystem in a grid search manner.
    The `BatchRun` handles paralellisation and storage of results for you.
    To perform a batch run, implement this abstract base class and implement
    the `perform_single_simulation()` method.

    Results will be stored in the `result_directory_name` and contain:

    - The simulation results (information of each time step) of each
        simulation will be stored in `/trajectories`.
    - Additionally, a summary of all simulations will be stored in the `batch_run_summary.csv`.

    Examples of how to use the `BatchRun` can be found in `examples/batch_run`.

    Args:
        parameter_space: Parameters which will be used to perform the simulations.
        result_directory_name: Name of directory where the results will be dumped.
        max_workers: Number of parallel tasks to be executed. This should be
            max the number of cores of your system. If the default value
            `None` is set, the maximum number of available cores is used.

    Example:
        ```python
        class CustomBatchRun(BatchRun):
            def __init__(
                    self,
                    result_directory_name,
                    parameter_space,
            ):
                super().__init__(parameter_space=parameter_space, result_directory_name=result_directory_name, max_workers=4)

            def _create_energy_system(self, parameters: dict) -> EnergySystem:
                ...
                return energy_system


            def perform_single_simulation(self, parameters: dict) -> Tuple[pd.DataFrame, dict]:  # SimulationResults, Summary
                energy_system = self._create_energy_system(parameters)
                controller = SelfConsumption()
                simulation = Simulation(controller=controller, energy_system=energy_system)
                single_run_trajectory = simulation.run()

                economic_summary = nrgise.economics.get_economic_summary(...)

                # include whatever is of interest in the summary, e.g. parameters and economic summary
                summary = {
                    'parameters': parameters,
                    'economics': asdict(economic_summary)        }

                return single_run_trajectory, summary

        if __name__ == '__main__':
            parameter_space = {
                'storage_capacity': [0, 10, 20, 40, 60],
                'storage_efficiency': [0.8, 0.9],
            }

            batch_run = MyBatchRun(
                result_directory_name='tmp',
                parameter_space=parameter_space
            )
            batch_run.run()

            # investigate results
            results = pd.read_csv('tmp/batch_run_summary.csv', index_col=[0])
            ...
        ```
    """

    def __init__(self,
                 parameter_space: dict[str, Any],
                 result_directory_name: str,
                 store_trajectories: bool = True,
                 max_workers: Optional[int] = None):
        self._max_workers = max_workers
        self._result_directory_name = result_directory_name
        self._parameter_space = parameter_space
        self._store_trajectories = store_trajectories

        if not os.path.exists(result_directory_name + "/trajectories/"):
            os.makedirs(result_directory_name + "/trajectories/")

    def _single_simulation_wrapper(self, parameters: dict, iteration_index: int) -> dict:
        """
        Wraps the execution of `perform_single_run()` and enhances it by:
        1. Storing the trajectory data as .csv
        2. Adding the `iteration_index` as `run_id` so the stored trajectory can be mapped to the summary later.

        Args:
            parameters: Contains the parameters used in `single_run()` to e.g. construct an EnergySystem.
            iteration_index: Index which is used to map the summary results to the trajectory later.
        """

        single_run_trajectory, single_run_summary = self.perform_single_simulation(parameters)
        if self._store_trajectories:
            single_run_trajectory.to_csv(self._result_directory_name + '/trajectories/' + str(iteration_index) + '.csv')

        single_run_summary['run_id'] = iteration_index
        return flatten_dict(single_run_summary)

    @abstractmethod
    def perform_single_simulation(self, parameters: dict) -> Tuple[pd.DataFrame, dict[str, Any]]:
        """
        Contains implementation of a single simulation run. This typically includes the construction and simulation
        of an EnergySystem dependent on the `parameters`. Returns results of the simulation in two parts:

        Returns:
            Full simulation results of the single run as a pd.DataFrame.
            Summary of the single run as dicts. The summary will be used to
                create the `batch_run_summary.csv` of the whole batch run later.
        """
        pass

    def run(self) -> None:
        """
        Starts the batch run. This will execute `perform_single_run()` for all parameter combinations in the `parameter_space`.
        """
        start_time = time.time()

        param_names = list(self._parameter_space.keys())
        param_values = list(self._parameter_space.values())

        amount_of_combinations = len(list(itertools.product(*param_values)))
        print('Running {n} simulations'.format(n=amount_of_combinations))
        batch_run_summary = []
        with (tqdm(total=len(list(itertools.product(*param_values)))) as progress_bar,
              ProcessPoolExecutor(max_workers=self._max_workers) as executor):
            single_simulation_future_results = []
            for i, combination in enumerate(itertools.product(*param_values)):
                parameters = dict(zip(param_names, combination))
                single_simulation_future_result = executor.submit(self._single_simulation_wrapper, parameters, i)
                single_simulation_future_results.append(single_simulation_future_result)
            for result in as_completed(single_simulation_future_results):
                batch_run_summary.append(result.result())
                progress_bar.update(1)

        batch_run_summary_df = self._post_process_batch_run_summary(batch_run_summary)
        batch_run_summary_df.to_csv(self._result_directory_name + '/batch_run_summary.csv', index=False)
        environment_dependencies_df = get_environment_dependencies()
        _write_environment_dependencies_as_txt(environment_dependencies_df,
            file_path=self._result_directory_name + '/requirements.txt')
        print('Execution time batch run: ' + str(time.time() - start_time) + ' seconds')

    @staticmethod
    def _post_process_batch_run_summary(batch_run_summary: list[dict]) -> pd.DataFrame:
        batch_run_summary_df = pd.DataFrame.from_records(batch_run_summary)
        sorted_summary = batch_run_summary_df.sort_values(by=['run_id'])
        # Make sure 'run_id' is displayed first in summary
        return sorted_summary[['run_id'] + [col for col in sorted_summary.columns if col != 'run_id']]
