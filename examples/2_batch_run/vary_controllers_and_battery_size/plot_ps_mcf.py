import sys

import pandas as pd
from matplotlib import pyplot as plt


def generate_npv_vs_capacity_plot(result: pd.DataFrame, results_dir_path: str = 'results'):
    # NPV per Controller and capacity for a fixed installed PV Peak Power
    def shorten_controller_name(grouped_index_string):
        """
        extract controller name from grouped pandas index
        """
        controller_name = grouped_index_string[0]
        short_con_name = str.split(controller_name, '<class ')[1].split("'>")[0].split(".")[-1]  #
        threshold = grouped_index_string[1]
        return short_con_name + ', ' + str(threshold)

    fig, ax = plt.subplots()
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.1, hspace=0.01)

    plot_data = result[result['parameters.capacity'] < 250]

    grouped_dataframe = plot_data.groupby(['parameters.controller.class', 'parameters.controller.threshold']).agg(list)
    for index, row in grouped_dataframe.iterrows():
        ax.plot(row['parameters.capacity'], row['economics.npv'], label=shorten_controller_name(index))
    ax.set_ylabel('NPV (€)', fontsize=14)
    ax.set_xlabel('Capacity in kWh', fontsize=14)
    plt.title("NPV of runs")
    ax.grid(True)
    fig.legend(loc="lower left")
    plt.tight_layout()
    plt.show(block=not sys.stdin.isatty())
    plt.savefig(results_dir_path + '/npv_plot_with_full_cycles.jpg')
