import sys

import pandas as pd
from matplotlib import pyplot as plt


def plot(result: pd.DataFrame):
    fig, ax = plt.subplots()
    ax.step(result.index, result['uncontrolled_power_contribution_per_component.load'] * -1, where="post", label='Load')
    ax.step(result.index, result['uncontrolled_power_contribution_per_component.pv'], where="post", label='Generation')
    ax.step(result.index, result['grid_builder_usage'], where="post", label='Grid usage')
    ax.step(result.index, result['power_applied'], where="post", label='Battery Power')
    ax.set_xlabel("Time")
    ax.set_ylabel('Power in kW', fontsize=14)
    ax.grid(True)
    fig.legend(
        prop={'size': 10},
    )
    plt.title("15-minute Power flows")
    plt.show(block=not sys.stdin.isatty())
