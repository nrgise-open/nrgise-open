from nrgise.common.constants import SECONDS_PER_YEAR
from nrgise.components.storage.helper import calc_equivalent_cycle
from nrgise.components.storage.storage_abc import StorageABC
from nrgise.components.storage.storage_wrapper_abc import StorageWrapperABC


class AgingLinearCapacityWrapper(StorageWrapperABC):
    """
    A wrapper for a `StorageABC` which implements a linear aging model.
    This Aging Model performs cyclic and calendric aging linearly.
    For both the calendric and the cyclic aging, the capacity decrease is calculated.
    However, only one of the two factors is used to age the capacity:
    the one that caused the larger loss in the state of health (which is due to
    the fact that both parameters `max_cycles` and `lifetime_in_years` are intertwined anyway).

    Note: The cycling counting is done by the actual capacity and not by the initial capacity here!
    Keep in mind that reducing the capacity also reduces the absolute electricity in the storage.

    Args:
        eol: Defines the fraction of capacity which is available when the
            storage reaches its maximum lifetime or maximum cycles
        replace_storage_when_eol_reached: Replaces the storage by calling
            the `reset()` method when maximum lifetime or cycles are reached. This might be
            used in longer simulation periods where storage replacements are
            considered.
        storage: The `StorageABC` which should be wrapped to perform linear aging
        lifetime_in_years: The maximum lifetime of the storage in years. After
            this time, the storage is considered to be at its end of life (EOL).
        max_cycles: The maximum number of equivalent cycles the storage can
            perform before it is considered to be at its end of life (EOL).

    Example:
        ```python
        battery = StorageSystemEnergyReservoir(...)

        aging_battery = AgingLinearCapacityWrapper(
            storage=battery,
            lifetime_in_years=10,
            max_cycles=7000,
            eol=0.7,
            replace_storage_when_eol_reached=True,
        )

        es.add_components(..., aging_battery)
        ```
    """

    def __init__(
            self,
            storage: StorageABC,
            lifetime_in_years: float,
            max_cycles: int,
            eol: float,
            replace_storage_when_eol_reached: bool = False,
        ) -> None:
        if not isinstance(storage, StorageABC):
            raise TypeError
        # Super constructor call creates, among other fields, the self.storage property which includes the storage
        super().__init__(storage=storage)
        self._eol = eol
        self._lifetime_in_years = lifetime_in_years
        self._max_cycles = max_cycles
        self._equivalent_cycles = 0.0
        self._storage_age_seconds = 0.0
        self._soh = 1.0
        self._initial_capacity = self.storage.capacity
        self._cycling_soh_loss = 0.0
        self._calendric_soh_loss = 0.0
        self._replace_storage_when_eol_reached = replace_storage_when_eol_reached

    def set_power_contribution(self, power: float) -> float:
        power_contribution = self.storage.set_power_contribution(power)
        self._equivalent_cycles += calc_equivalent_cycle(
            power=power_contribution,
            time_delta_seconds=self.storage.time_delta_seconds,
            # Note: The cycling counting is done by the actual capacity and not by the initial capacity here !
            energy_capacity=self.storage.capacity,
        )
        self._storage_age_seconds += self.storage.time_delta_seconds

        self._cycling_soh_loss = self.calculate_cyclic_aging_based_soh_loss(
            self._eol, self._equivalent_cycles, self._max_cycles)

        storage_age_in_years = self._storage_age_seconds / SECONDS_PER_YEAR
        self._calendric_soh_loss = self.calculate_calendric_aging_based_soh_loss(
            self._lifetime_in_years, self._eol, storage_age_in_years)

        self._soh = self.calculate_soh(self._cycling_soh_loss, self._calendric_soh_loss, self._eol)
        self.storage.capacity = self._initial_capacity * self._soh
        if self._replace_storage_when_eol_reached:
            self._handle_storage_replacement()
        return power_contribution

    def get_state(self) -> dict[str, float]:
        return {
            **self.storage.get_state(),
            'soh': self._soh,
            'cycling_soh_loss': self._cycling_soh_loss,
            'calendaric_soh_loss': self._calendric_soh_loss,
            'capacity': self.storage.capacity,
            'equivalent_cycles': self._equivalent_cycles,
        }

    def reset(self) -> None:
        self.storage.reset()
        self._soh = 1.0
        self.storage.capacity = self._initial_capacity
        self._equivalent_cycles = 0.0
        self._cycling_soh_loss = 0.0
        self._calendric_soh_loss = 0.0
        self._storage_age_seconds = 0.0

    @staticmethod
    def calculate_cyclic_aging_based_soh_loss(eol: float, equivalent_cycles: float, max_cycles: float) -> float:
        if equivalent_cycles > max_cycles:
            return 1 - eol
        return (1 - eol) * equivalent_cycles / max_cycles

    @staticmethod
    def calculate_calendric_aging_based_soh_loss(lifetime: float, eol: float, storage_age: float) -> float:
        if storage_age > lifetime:
            return 1 - eol
        return (1 - eol) * storage_age / lifetime

    @staticmethod
    def calculate_soh(cycling_soh_loss: float, aging_soh_loss: float, eol: float) -> float:
        # Consider only the stronger of the two aging effects. Alternatively,
        # both aging effects can be combined, but this tends to overestimate aging.
        soh_loss = max(cycling_soh_loss, aging_soh_loss)
        # Limit soh by the eol criteria
        return max(1 - soh_loss, eol)

    def _handle_storage_replacement(self) -> None:
        if self._soh == self._eol:
            self.reset()

    @property
    def soh(self) -> float:
        return self._soh

    @property
    def initial_capacity(self) -> float:
        return self._initial_capacity

    @property
    def equivalent_cycles(self) -> float:
        return self._equivalent_cycles
