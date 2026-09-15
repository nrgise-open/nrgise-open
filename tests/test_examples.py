import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIRECTORY = REPOSITORY_ROOT / 'examples'


@pytest.mark.parametrize(
    'relative_script_path',
    [
        pytest.param(
            Path('1_self_consumption_and_economics/self_consumption_and_economics.py'),
            id='self-consumption',
        ),
        pytest.param(
            Path('2_batch_run/self_consumption_vary_battery_and_pv_size/'
                 'self_consumption_vary_battery_and_pv_size.py'),
            id='battery-pv-batch',
        ),
        pytest.param(
            Path('2_batch_run/vary_controllers_and_battery_size/vary_controllers_and_battery_size.py'),
            id='controller-battery-batch',
        ),
        pytest.param(Path('3_advanced/aging_battery/aging_battery.py'), id='aging-battery'),
        pytest.param(Path('3_advanced/fast_charger/fast_charger.py'), id='fast-charger'),
        pytest.param(Path('3_advanced/mpc/mpc_time_of_use.py'), id='mpc-time-of-use'),
    ],
)
def test_example_script(relative_script_path: Path):
    with TemporaryDirectory() as temporary_directory:
        copied_examples_directory = Path(temporary_directory) / 'examples'
        shutil.copytree(
            EXAMPLES_DIRECTORY,
            copied_examples_directory,
            ignore=shutil.ignore_patterns('results', '__pycache__'),
        )
        script_path = copied_examples_directory / relative_script_path

        # refactored using gpt 5.6 sol
        environment = os.environ.copy()
        environment['MPLBACKEND'] = 'Agg'
        existing_python_path = environment.get('PYTHONPATH')
        environment['PYTHONPATH'] = os.pathsep.join(
            path for path in (str(REPOSITORY_ROOT), existing_python_path) if path
        )

        try:
            subprocess.run(
                [sys.executable, str(script_path)],
                cwd=script_path.parent,
                check=True,
                capture_output=True,
                text=True,
                timeout=500,
                env=environment,
            )
        except subprocess.CalledProcessError as error:
            pytest.fail(
                f'Example failed with exit code {error.returncode}.\n'
                f'stdout:\n{error.stdout}\n'
                f'stderr:\n{error.stderr}',
                pytrace=False,
            )
