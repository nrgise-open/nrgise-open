# Analyse Results

When running a simulation (`Simulation.run()`), step-wise results are returned
for the full time horizon.

This means every simulation time step is available for post-processing, so you
can build any analysis you need (plots, custom computations, validation,
etc.).

It is important to note that controllers can pass additional custom
information: the second return value of `Controller.get_action(state)` is
stored in the simulation results as `additional_control_info`. With this,
arbitrary controller-side context can be logged.

The field `grid_builder_usage` in the results logs the power which was supplied or fed into the
`GridBuilder` (e.g. a "normal" grid connection point `Grid`) in each time step 
(positive=getting power from the grid, negative=feeding in).

## Economics

For economic post-processing, *NRGISE Open* provides the [Economics API](../api/economics/core.md), which can
be applied to simulation results.

In practice, economic evaluation is typically performed over multiple years of
operation. To do so, there are two common options:

1. **Simulate the full investment horizon (for example 10 years).**

    This is typically the most accurate option, but it requires time-series
    data over the full horizon. If you want to simulate multiple years while
    only having a one-year data profile (for example, to include storage
    aging effects), you can use
    [`EnergySystem.stretch_time()`](../api/energy-system.md/#nrgise.EnergySystem.stretch_time)
    before running the simulation.

    Note that this increases computational effort. This is especially relevant
    for large simulation studies, for example with [Batch Run](batch-run.md).


2. **Simulate one representative year and stretch the results in post-processing.**

    In this option, the actual simulation uses a shorter representative horizon
    (usually one year). The resulting time series is then stretched to match
    the investment horizon of interest.

    For this workflow, use the economics helper
    [`stretch_data_over_investment_horizon(...)`](../api/economics/helper.md/#nrgise.economics.helper.stretch_data_over_investment_horizon)
    to stretch the parts of the results that are relevant for your economic calculations.

In most cases, cash flow must be calculated for the energy system.
For Commercial & Industry and residential use cases, cash flow is often
primarily defined by the yearly electricity bill.
For this, dedicated helper functions are available for cash-flow calculations
with tariff-based grid-charge modeling.

For an example workflow, see the economics example.

In most cases, it is recommended to use the [economic summary](../api/economics/summary.md/#nrgise.economics.summary.EconomicSummary)
from the economics module, because it aggregates the cash-flow-based
evaluation into useful KPIs (amortisation time, NPV, ...).

Also, in many cases a baseline simulation is helpful when computing the
economic summary, because you may want to compare your setup against a
reference setup. For example, if you want to evaluate whether storage makes
sense (or which storage is best), a common baseline is the same energy system
without storage.
