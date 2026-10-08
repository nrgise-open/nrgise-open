# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from abc import ABC, abstractmethod

from nrgise.common.types import Bus, PowerContribution
from nrgise.components.capabilities.controllable_mixin import ControllableMixin
from nrgise.components.capabilities.publishes_state_mixin import PublishesStateMixin


class StorageABC(ControllableMixin, PublishesStateMixin, ABC):
    """
    Base class for storage components.
    """
    # IMPORTANT!
    # In case new instance variables are introduced,
    # make sure to update the storage wrappers, so they expose the new instance variables as well!
    @property
    @abstractmethod
    def time_delta_seconds(self) -> int:
        pass

    @property
    @abstractmethod
    def capacity(self) -> float:
        """in kWh"""
        pass

    @capacity.setter
    @abstractmethod
    def capacity(self, value: float) -> None:
        # used for aging
        pass

    @property
    @abstractmethod
    def soc(self) -> float:
        pass

    @property
    @abstractmethod
    def power_bus(self) -> Bus:
        pass

    @abstractmethod
    def set_power_contribution(self, power: float) -> PowerContribution:
        """
        Sets the power (kW) of the storage during the upcoming simulated time step.
        Positive values cause a discharge of the storage, whereas negative values cause a charge.

        Args:
            power: The amount of power (kW) to charge or discharge. Positive = discharge; Negative = charge.
        Returns:
            Actual power charged or discharged by the storage on its power bus.
        """

    @staticmethod
    def _enforce_power_limit(power: float, nominal_power: float) -> float:
        """
        Cuts the requested amount of power to the amount of power which can be handled by the battery.
        Args:
            power: Amount of power requested
            nominal_power: Max amount of power which can be handled by the battery.
        Returns:
            Requested power which is guaranteed to lie in the nominal power bound.
        """
        return min(power, nominal_power) if power >= 0 else max(power, -nominal_power)
