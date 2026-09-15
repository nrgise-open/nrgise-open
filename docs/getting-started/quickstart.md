
# Running a Simulation at a glance

```python
from nrgise import EnergySystem, Simulation
from nrgise.components import Battery, Grid, Load, Pv
from nrgise.controllers import SelfConsumptionController

# Create a energy system and its components
es = EnergySystem(time_index=data.index)
grid = Grid(label='grid')
load = Load(label='load', power_profile=load_profile)
pv = Pv(label='pv', power_profile=generation_profile)
battery = Battery(
    label='battery',
    time_delta_seconds=es.time_delta_seconds,
    nom_power=200,
    capacity=800
)
es.add_components(grid, load, battery, pv)

# Define a controller
controller = SelfConsumptionController(storage_label='battery')

# Run the simulation
simulation = Simulation(energy_system=es, controller=controller)
results = simulation.run()
```

# Examples 

To give you an introduction to *NRGISE Open*, we have provided you with some [examples](https://gitlab.cc-asp.fraunhofer.de/iseels/asy/nrgise/-/tree/main/examples?ref_type=heads). Note that the examples are only tested with the latest available version of *NRGISE Open*.


