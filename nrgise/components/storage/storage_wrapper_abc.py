from abc import ABC

from nrgise.components.storage.storage_abc import StorageABC


class StorageWrapperABC(StorageABC, ABC):
    """
    Used to implement wrappers which extend the functionality of a `StorageABC`.
    It is an implementation of the decorator pattern.
    The pattern was used for a similar usage in gymnasium: https://gymnasium.farama.org/_modules/gymnasium/core/#Wrapper
    """

    def __init__(self, storage: StorageABC) -> None:
        self.storage = storage

    @property
    def capacity(self) -> float:
        return self.storage.capacity

    @capacity.setter
    def capacity(self, value: float) -> None:
        # used for aging
        self.storage.capacity = value

    @property
    def soc(self) -> float:
        return self.storage.soc

    @property
    def label(self) -> str:
        return self.storage.label

    @property
    def time_delta_seconds(self) -> int:
        return self.storage.time_delta_seconds
