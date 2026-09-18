import sys

import pandas as pd
from matplotlib import pyplot as plt


def investigate_top_runs(result, results_dir_path: str = 'results'):
    fig, ax = plt.subplots()

    line_labels = result['parameters.capacity'].unique()

    for line_label in line_labels:
        line_plot_data = result[result['parameters.capacity'] == line_label]
        line_plot_data = line_plot_data.sort_values(by=['run_id'])
        ax.plot(
            line_plot_data['parameters.pv_peak_power'],
            line_plot_data['economics.npv'],
            label=line_label,
        )

    ax.set_ylabel('NPV in €', fontsize=14)
    ax.set_xlabel('PV size in kWp', fontsize=14)
    ax.grid(True)
    fig.legend(title="Storage Capacity in kWh",
               prop={'size': 10},
               title_fontsize=10)
    plt.title("NPV of runs")
    plt.tight_layout()

    plt.show(block=not sys.stdin.isatty())
    fig.savefig(results_dir_path + "/comparison_between_runs.jpg")


def investigate_optimal_run(result, results_dir_path: str = 'results'):
    optimal_run = result.iloc[result['economics.npv'].idxmax()]
    run_data = pd.read_csv(results_dir_path + '/trajectories/' + str(int(optimal_run.run_id)) + '.csv',
                           index_col=[0], parse_dates=True)

    plot_data = run_data[1500:2000]
    plot_x_data = run_data[1500:2000].index
    fig, ax = plt.subplots()
    ax.step(plot_x_data,plot_data['uncontrolled_power_contribution_per_component.load'], where="post", label='Load')
    ax.step(plot_x_data,plot_data['uncontrolled_power_contribution_per_component.pv'], where="post", label='Generation')
    ax.step(plot_x_data,plot_data['grid_builder_usage'], where="post", label='Grid usage')
    ax.step(plot_x_data, plot_data['power_applied'], where="post", label='Battery Power')
    ax.set_ylabel('Power in kW', fontsize=14)
    ax.grid(True)
    ax.set_xlabel("Time", fontsize=14)

    fig.legend(prop={'size': 10})
    plt.title("Behavior of Best Run")
    plt.tight_layout()
    plt.show(block=not sys.stdin.isatty())
    fig.savefig(results_dir_path + "/best_run_behavior.jpg")
