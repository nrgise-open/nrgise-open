from datetime import datetime, timedelta

import pandas as pd


def charge_event_dict_to_pandas_profile(data_dict, timeseries):
    """ Uses a compact charge event dictionary to create a time series profile as needed by ``ChargePoint``.

       Args:
           data_dict: Charge-event data containing ``time_stamp``,
               ``soc_arrival``, ``capacity``, and ``parking_time_minutes``.
           timeseries: Simulation timestamps.

       Returns:
           A DataFrame indexed by ``timeseries``. Non-null ``soc_arrival`` and
           ``capacity`` values indicate an occupied charge point.
       """
    # Convert timestamp strings to datetime objects
    timestamps = [datetime.strptime(ts, '%d.%m.%Y %H:%M') for ts in data_dict['time_stamp']]

    # Create an empty DataFrame to store the mapped values
    df = pd.DataFrame(index=timeseries)  # noqa PD901

    # Iterate over each timestamp and value pair
    pairs = zip(timestamps,
                data_dict['soc_arrival'],
                data_dict['capacity'],
                data_dict['parking_time_minutes'])
    for ts, soc_arrival, capacity, parking_time_minutes in pairs:
        # Calculate the range of adjacent timestamps based on time in minutes
        range_start = ts
        range_end = ts + timedelta(minutes=parking_time_minutes)
        occupied = (
        (df.index >= range_start)
            & (df.index < range_end)
        )
        # Assign the values to the timestamps within the range in the DataFrame
        df.loc[occupied, 'soc_arrival'] = soc_arrival  # type: ignore[index, misc]
        df.loc[occupied, 'capacity'] = capacity  # type: ignore[index, misc]

    return df
