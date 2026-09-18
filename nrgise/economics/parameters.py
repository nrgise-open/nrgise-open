# Sources for parameters see: https://doi.org/10.1016/j.apenergy.2025.125353
DEFAULT_MAINTENANCE_COST_FACTOR = 0.02
DEFAULT_INVESTMENT_HORIZON = 10
DEFAULT_DISCOUNT_RATE = 0.079
DEFAULT_STORAGE_REPLACEMENT_COST_FACTOR = 0.412

WARNING_FOR_UNSTRETCHED_SIMULATION_RESULTS = \
    'Your Cash FLow has length 1, meaning only one year of operation is taken into account when calculating the ' \
    'economic summary. If your investment horizon is greater then 1 year, make sure to increase the length of your ' \
    'input data when calculating the cash flow (e.g. by using `stretch_data_over_investment_horizon()`). See the ' \
    'basic economics example for more details.'
