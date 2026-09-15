# Extending NRGISE

## Adding a New Component

NRGISE uses a capability-based component model:

- Every component must implement the base `ComponentABC` contract.
- Optional capabilities are added by inheriting dedicated mixins (abstract base classes).
- `EnergySystem` and `State` discovers capabilities via `isinstance(...)` checks and integrate components accordingly.

This keeps components modular and avoids one large base class with many optional methods.

### Base Contract: `ComponentABC`

Every component must inherit from `nrgise.components.ComponentABC` and implement:

- `label` property: unique identifier in an `EnergySystem`
- `reset()` method: Called at the start of a simulation to restore initial state.
Minimal template:

```python
from nrgise.components import ComponentABC


class MyComponent(ComponentABC):
	def __init__(self, label: str):
		self._label = label

	@property
	def label(self) -> str:
		return self._label

	def reset(self):
		pass
```

### Add Components Capabilities Using Mixins

Mixins define optional capabilities. You can combine multiple mixins in one component.

- `ControllableMixin` makes components receive a control action through `set_power_contribution(...)` and must return the power they actually contributed (power asked for via an action could differ from power returned, e.g. asking for power from an empty battery).
- `TimeStepAwareMixin` makes components be notified when the simulation advances to the next time step via `handle_time_step_update(...)`. This might be used for components having an internal data profile which needs to be advanced according to the new time step.
- `DataProfileMixin` marks a component as having an associated data profile. Unlike the other mixins, it does not affect the simulation itself. Instead, it is used by utility functions and validation logic, for example to ensure that all data profiles in an `EnergySystem` have the same length or to enable `EnergySystem.stretch_time()`.
- `ContributesToPowerBalanceMixin` makes components add their uncontrollable power contribution (kW) via `uncontrolled_power_contribution()` to the `State` in each time step.
- `PublishesStateMixin` makes the component dump arbitrary information (dict) into `State` through `get_state()` to be visible to the controller and in the results.
  
**Note:** Both `ContributesToPowerBalanceMixin` and `PublishesStateMixin` contribute information to the `State`, which is passed to the controller to compute the action. However, they serve different purposes. `ContributesToPowerBalanceMixin` contributes a well-defined physical quantity: the component's uncontrollable power contribution (in kW) for the current time step (positive: adding power; negative: taking power). `PublishesStateMixin`, on the other hand, allows arbitrary information to be exposed as a dictionary.

**Additional Information**

- More detailed docs for all mixins see: [API Docs](../api/components/components.md).
- For a detailed view of how each mixin causes the component to be included where in the simulation flow see: [Simulation Flow](simulation-flow.md).

### Example: New Component

The example below shows a controllable electric heater which dumps information into the system state (meaning the controller could perform actions based on the temperature_c).

```python
from typing import Any

from nrgise.components import ControllableMixin, PublishesStateMixin


class ElectricHeater(ControllableMixin, PublishesStateMixin):
    def __init__(self, label: str, initial_temperature_c: float = 20.0):
        self._label = label
        self._initial_temperature_c = initial_temperature_c
        self._temperature_c = initial_temperature_c

    @property
    def label(self) -> str:
        return self._label

    def reset(self):
        self._temperature_c = self._initial_temperature_c

    def set_power_contribution(self, power: float) -> float:
        # Positive = inject to system, negative = consume from system.
        # A heater consumes power, so we limit to non-positive values.
        assert power <= 0.0, "Heater can only consume power (negative values)."

        # Very simple thermal model example.
        self._temperature_c += (-power) * 0.01
        return power

    def get_state(self) -> dict[str, Any]:
        return {
            "temperature_c": self._temperature_c,
        }
```

### Common Pitfalls

- Non-unique labels: `EnergySystem.add_components(...)` requires unique labels.
- Mismatched action count: number of controller actions must match controllable components of energy system.
- Wrong sign convention: positive/negative direction should match NRGISE convention.
- Missing reset logic: stale state carries across runs.
- Data profile length mismatch vs `EnergySystem.time_index`.


## Adding a New Controller

Add a controller by implementing the `ControllerABC` abstract base class and its `get_action(state)` method.

During simulation, the controller receives the current `State` in  each time step and return the power which should be 
contributed to the energy system in this time step. Note that it is just a request to the *Controllable* component and the actual power contributed can be different.

Whenever `get_action(state)` is called, it returns: 

- A dict mapping `controllable_label -> requested power contribution in kW`
- Optional additional information, which is stored in simulation results.

### Minimal example:

```python
from typing import Any

from nrgise.common.state import State
from nrgise.controllers import ControllerABC


class MyController(ControllerABC):
    def __init__(self, storage_label: str):
        self._storage_label = storage_label

    def get_action(self, state: State) -> tuple[dict[str, float], Any]:
        # Example: compensate current uncontrolled power balance
        power_setpoint = -1 * state.uncontrolled_power_balance

        action = {
            self._storage_label: power_setpoint,
        }
        controller_info = {
            "strategy": "balance",
        }
        return action, controller_info
```

### Important Checks

- Return power values in **kW** using NRGISE sign convention
    (positive: contributes power to the system,
    negative: consumes power from the system).
- Ensure the returned dict keys are labels of controllable components in the
    `EnergySystem`.
- Ensure action count matches number of controllables
    (one action per controllable).
- Remember that requested power and actually applied power can differ due to
    component constraints.

## Injecting Custom Logic into the Simulation Flow

You can inject custom logic into a running simulation by registering a hook
with `Simulation.register_hook(...)`. The hook is executed after each
simulation step and receives the simulation object and the current step result.

For details (including the exact hook function signature), see
[Simulation API](../api/simulation.md#nrgise.Simulation.register_hook).

