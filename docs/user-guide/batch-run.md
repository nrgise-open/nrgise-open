# Batch Run

A batch run is a larger simulation study where multiple simulations are
executed in parallel.

You define a parameter space and run all parameter combinations in a
grid-search fashion.

Typical motivation for using a batch run:

- Parameter sweeps and sensitivity studies.
- Built-in parallelisation for faster execution.
- Structured results output: an overview summary plus detailed time-step-sharp
	trajectories per simulation run.

For API usage and implementation details, see
[Batch Run API](../api/batch-run.md).
