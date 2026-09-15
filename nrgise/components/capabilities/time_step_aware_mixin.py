from abc import ABC, abstractmethod

from nrgise.components.component_abc import ComponentABC


class TimeStepAwareMixin(ComponentABC, ABC):
    """
    Mixin for components that react to simulation time-step updates.
    """

    @abstractmethod
    def handle_time_step_update(self, time_step: int) -> None:
        """
        Notify the component that the simulation advanced to `time_step`.
        Logic which updates the component according to the new time step should
        be implemented here.

        Args:
            time_step: The new time step.
        """
        pass
