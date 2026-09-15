## Simulation

The `Simulation` class orchestrates the time-step loop over the energy system horizon.
For each step, it obtains a control action, advances the system, performs grid balancing,
and stores the resulting step data.

**The detailed simulation flow is documented in the user guide section**
[Simulation Flow](../user-guide/simulation-flow.md).

::: nrgise.Simulation
