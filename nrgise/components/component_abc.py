from abc import ABC, abstractmethod


class ComponentABC(ABC):
    """
    Base class for all components that can be added to an `EnergySystem`.
    """

    @property
    @abstractmethod
    def label(self) -> str:
        """
        Unique identifier of the component within an `EnergySystem`.

        The label is used to identify the component in the `State`,
        simulation results, and is used to dispatch the action from the controller to the component
        (if it implements `ControllableMixin`).
        """

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the component to its initial state.

        This method is called at the beginning of each simulation to ensure
        that multiple simulation runs start from identical initial conditions.
        """
