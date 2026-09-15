from abc import ABC, abstractmethod

from nrgise.common.types import GenericSequence
from nrgise.components.component_abc import ComponentABC


class DataProfileMixin(ComponentABC, ABC):
    """
    Mixin for components with an associated data profile.

    This mixin does not affect the simulation itself. Instead, it enables
    utility functions and validation logic.
    """

    @property
    @abstractmethod
    def data_profile(self) -> GenericSequence:
        """
        Return the component's data profile.
        """
        pass

    @data_profile.setter
    @abstractmethod
    def data_profile(self, value: GenericSequence) -> None:
        """
        Set the component's data profile.
        """
        pass
