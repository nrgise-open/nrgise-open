from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from nrgise.common.state import State


class ControllerABC(ABC):
    """
    Defines the base class for all controllers.
    """

    @abstractmethod
    def get_action(self, state: State) -> Tuple[Dict[str, float], Any]:
        """
        Returns the action(s) to be taken by the *Component(s)* implementing `ControllableMixin` in the
        EnergySystem. An action defines the amount of kW which *Component* implementing `ControllableMixin`
        should contribute to the energy system in the current time step
        (positive = contributing power to the energysystem;
        negative = taking power).

        Args:
            state: Current `State` of the EnergySystem

        Returns:
            Mapping from label of the `ControllableMixin` to the amount of kW which
                should be contributed (positive = discharging) in the current time step.
            Additional controller information, which is available in simulation results for later analysis.
        """
