import os
import sys
from typing import Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def read_and_preprocess_data() -> Tuple[np.ndarray, np.ndarray, pd.Index]:
    load_pv_data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data/load_and_pv.csv')
    data = pd.read_csv(load_pv_data_path, index_col=['time'], parse_dates=True)
    load_profile = data['load']

    day_ahead_prices_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data/synthetic_day_ahead_prices_2019.csv')
    data = pd.read_csv(day_ahead_prices_path, index_col=['Datum (MEZ)'], parse_dates=True)
    price_profile = data['Day Ahead Auktion']
    price_profile.index = pd.to_datetime(price_profile.index, utc=True)
    price_profile.index = price_profile.index + pd.Timedelta('1h')
    price_profile = price_profile.resample('900s').ffill()
    price_profile_eur_kwh = price_profile/1000 #from EUR/MWh to EUR/kWh

    return np.array(load_profile), np.array(price_profile_eur_kwh), load_profile.index


def plot_tou(results, price_profile):
    _fig1 = plt.figure()
    ax = plt.subplot()

    # Use index for consistent x-axis location of the data
    x_vals = results.index

    ax.step(x_vals, results['uncontrolled_power_balance'] * -1, where='post', label='Residual Load')
    ax.step(x_vals, np.array(price_profile)*1000, '--', where='post', label='Price')
    ax.step(x_vals, results['grid_builder_usage'], where='post', label='Grid Usage')
    ax.step(x_vals, results['power_requested'], where='post', label='Battery Power')
    plt.ylabel('Power Flows (kW) & Price (EUR per MWh)')
    plt.xlabel('Time Step')
    plt.title("Time of Use Price and Power Flows")
    ax.legend()
    ax.grid()
    plt.show(block=not sys.stdin.isatty())
    return _fig1
