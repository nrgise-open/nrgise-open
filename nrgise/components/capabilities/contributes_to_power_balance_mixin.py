# Assisted-by: OpenCode:fhgenie-pro/gpt-5.6-sol
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Mapping

from nrgise.components.component_abc import ComponentABC

if TYPE_CHECKING:
    from nrgise.common.types import Bus


class ContributesToPowerBalanceMixin(ComponentABC, ABC):
    """Capability for components with uncontrolled power contributions."""

    @abstractmethod
    def uncontrolled_power_contributions(self) -> Mapping[Bus, float]:
        """Return the current uncontrolled power contribution per bus in kW.

        Positive values supply a bus; negative values consume power from it.
        """
        pass
