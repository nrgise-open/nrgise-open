from abc import ABC, abstractmethod
from typing import Any

from nrgise.components.component_abc import ComponentABC


class PublishesStateMixin(ComponentABC, ABC):
    """
    Mixin for components that publish information to the `State`.

    The published information is available to the controller for making
    control actions and is also included in the simulation results.
    """

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        """
        Returns:
            Component information to include in the global `State`. Arbitrary
            component information for the controller and simulation results.
        """
