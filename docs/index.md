<style>
.md-content__inner > h1:first-child {
	display: none;
}
</style>

![NRGISE Header Logo](imgs/logo.png)

*NRGISE Open* is a Python framework for simulating local energy systems over time.

It uses sequential time-step simulation to model the interaction between electrical components of the energy system and control strategies under realistic operating conditions. NRGISE provides ready-to-use components and controllers while remaining extensible, allowing researchers and engineers to implement custom models and controllers. Unlike optimization-focused frameworks, NRGISE is built around explicit controllers and rolling-horizon simulation, making it well suited for techno-economic assessments under realistic operating conditions.

## What you can do with *NRGISE Open*

- **Simulate common use cases out of the box:** Plug your PV and load data into our predefined examples to simulate use cases such as  self-consumption maximization and peak shaving without writing custom code.
- **Techno-economic assessments:** Evaluate how storage sizing, control strategies and system configurations affect technical and economic performance.
- **Develop and benchmark controllers:** Use NRGISE as a simulation environment for developing, testing, and benchmarking custom controllers, from simple rule-based strategies to model predictive control, reinforcement learning, and other advanced approaches.
- **Study impact of forecasting:** Integrate custom forecasting models into rolling-horizon simulations and investigate how forecast errors affect system operation and economic performance.
- **Run simulation studies at scale:** Execute parameter sweeps and batch simulations to compare hundreds or thousands of scenarios for sizing studies, sensitivity analyses, or scientific experiments.
- **Extend the framework:** Implement your own components, storage models, controllers, forecasters, aging models, or economic models using our well-defined interfaces.

## When another tool may be a better fit

- When you just want to see the mathematically optimal system layout without explicitly considering control strategies: Use an optimization-based tool like [oemof](https://oemof.org/), [ETHOS.FINE](https://vsa-fine.readthedocs.io/en/develop/) or [PyPSA](https://github.com/pypsa/pypsa)
- When you want to model sector coupling (electricity, heat and mobility): Use [oemof](https://oemof.org/) or [ETHOS.FINE](https://vsa-fine.readthedocs.io/en/develop/)
- When you need to model a large power grid: Use a spatially resolved tool like [PyPSA](https://github.com/pypsa/pypsa)
- When you want a deep dive into battery aging: Use [SimSES](https://gitlab.lrz.de/open-ees-ses/simses/)
- When you want to deploy your controller in real-time: Use a deployment tool like [OpenEMS](https://openems.io/) (however, NRGISE controllers can be coupled with it)

If none of these tools fit your list, see [OpenMod for a broader tool comparison](https://wiki.openmod-initiative.org/wiki/Overview_of_models)

## Quick Links

<div class="grid cards" markdown>

-   :material-play-circle: **Getting started**

    ---

    [:octicons-arrow-right-24: Installation](getting-started/install.md) 

    [:octicons-arrow-right-24: Quickstart](getting-started/quickstart.md)

-   :material-view-list: **Overview**

    ---

    Learn about the core design principles.

    [:octicons-arrow-right-24: Architecture overview](user-guide/core-design.md)

-   :material-api: **API Reference**

    ---

    Browse the API docs generated from Python docstrings.

    [:octicons-arrow-right-24: Open API reference](./api/energy-system.md)

-   :material-github: **Source Code**

    ---

    NRGISE source code 

    [:octicons-arrow-right-24: Repository](https://github.com/nrgise-open/nrgise-open)

</div>
