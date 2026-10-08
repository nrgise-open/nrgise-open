from abc import ABC, abstractmethod
from typing import Mapping

from nrgise.components.component_abc import ComponentABC


class ContributesToPowerBalanceMixin(ComponentABC, ABC):
    """Capability for components with uncontrolled power contributions."""

    @abstractmethod
    def uncontrolled_power_contributions(self) -> Mapping[str, float]:
        """Return the current uncontrolled power contribution per bus in kW.

        Positive values supply a bus; negative values consume power from it.
        """
        pass
