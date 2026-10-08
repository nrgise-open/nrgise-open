At a high level, the `Simulation` component iterates over time and coordinates the interaction between the Controller and the `EnergySystem` (and thus its containing components). The `EnergySystem` applies control actions, advances the simulation, and handles building of the resulting system state. The controller requests scalar power from each controllable without selecting a bus. Each controllable determines the buses to which its applied power contributes. Fixed production and consumption are represented separately through `ContributesToPowerBalanceMixin` and grouped by named power bus.

Conceptually, each simulation step consists of three stages:

1. State Building: A new `State` of the EnergySystem and all its components is built. The `State` contains (1) arbitrary information of components published through `PublishesStateMixin`, (2) uncontrolled power contributions per named bus provided through `ContributesToPowerBalanceMixin` and (3) information about the current date time and time step.
2. Control: Based on the `State`, the controller computes an action. The action is dispatched by the `EnergySystem` to all `ControllableMixin` components. These return a `PowerContribution` containing the power they were actually able to provide per bus (requested and provided power can differ, e.g. an empty battery cannot provide power).
3. Results: The simulation combines uncontrolled and applied controllable contributions per bus and records `power_balance_per_bus` before grid balancing. The `GridBuilder` supplies or absorbs the remaining imbalance on the default electricity bus only.

The diagram below shows the detailed control flow of a single simulation step.

![MDP](../imgs/flowchart_nrgise.drawio.png)

The blue boxes in the diagram represent the available mixins (see [Extending NRGISE](extending.md) for more details about mixins). The mixins indicate where a component participates in the simulation flow. For example, a component implementing `ControllableMixin` receives a control action, while a component implementing `ContributesToPowerBalanceMixin` or `PublishesStateMixin` is queried when the system state is built.

In more detail, the flow is as follows:

1. `Simulation` provides the current state `state_t` to `controller.get_action(state_t)`.
2. The controller returns `action_t` (plus optional additional info).
3. `Simulation` triggers the simulation of one time step in the `EnergySystem`.
4. Inside `EnergySystem`, the action is forwarded to all components implementing `ControllableMixin`. Each component returns the power that was actually applied as a bus-to-power `PowerContribution`. The component owns this bus assignment. Applied power may differ from requested power, for example due to power limits or state-of-charge constraints.
5. The internal time step is advanced to `t+1`. As part of this step, all components implementing `TimeStepAwareMixin` are notified via `handle_time_step_update(...)`.
6. The next state `state_t+1` is built. During this step, all components implementing `PublishesStateMixin` and `ContributesToPowerBalanceMixin` are queried for their contribution to the `State`.
7. `simulate_one_time_step(...)` returns `power_applied`, `state_t+1`, and `done` back to `Simulation`.
8. Back in `Simulation`, the default electricity bus is balanced via the `GridBuilder`. Other buses are currently reported without automatic balancing.
9. The results of this simulation step are recorded. This includes the state, requested power, bus-aware applied power, the pre-grid balance of every bus, power supplied by the `GridBuilder`, and any additional information returned by the controller. A single contribution is stored in the scalar `power_applied` column for convenience. Multiple contributions use flattened `power_applied.<bus>.<component>` columns.
10. The loop starts again.
