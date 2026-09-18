from nrgise.components.storage.storage_abc import StorageABC


class Battery(StorageABC):
    """
    A simple model of an energy storage. The model can be classified as energy reservoir model according to
    https://ieeexplore.ieee.org/document/8922750

    Args:
        label: An unique identifier for the component.
        nom_power: Maximum of power which can be handled by the storage in kW.
        capacity: The overall capacity of the storage in kWh.
        time_delta_seconds: The duration of one time step in seconds.
        initial_soc: State of charge, in [0,1]
        efficiency_charge: Defines the efficiency of the storage when charging.
            When set to 0.95, 5% of the energy is considered lost when
            charging.
        efficiency_discharge: Defines the efficiency of the storage when discharging.
    """

    def __init__(
            self,
            label: str,
            nom_power: float,
            capacity: float,
            time_delta_seconds: int,
            initial_soc: float = 0,
            efficiency_charge: float = 1,
            efficiency_discharge: float = 1,
        ) -> None:
        self._label = label
        self.nom_power = nom_power
        self._capacity = capacity
        self._time_delta_seconds = time_delta_seconds
        self._initial_soc = initial_soc
        self._soc = initial_soc
        self._efficiency_charge = efficiency_charge
        self._efficiency_discharge = efficiency_discharge

    def set_power_contribution(self, power: float) -> float:
        """
        Tries to apply requested power contribution (kW).

        1. Power limits are enforced.
        2. The state of charge is updated according to the applied power and the storage's capacity and efficiency.
        3. Power which was actually applied is returned.

        """
        capacity = self._capacity
        soc = self._soc
        efficiency_charge = self._efficiency_charge
        efficiency_discharge = self._efficiency_discharge
        time_delta_h = self._time_delta_seconds / 3600

        power = super()._enforce_power_limit(power, self.nom_power)

        if power > 0 and capacity != 0:  # Discharge
            virtual_soc = soc - 1 / efficiency_discharge * power * time_delta_h / capacity
            if virtual_soc >= 0:  # Enough energy in storage to provide power
                self._soc = virtual_soc
            else:  # Not enough energy in storage => Storage empty
                power = soc * capacity / time_delta_h * efficiency_discharge
                self._soc = 0

        elif power < 0 and capacity != 0:  # Charging
            virtual_soc = soc + efficiency_charge * - power * time_delta_h / capacity
            if virtual_soc <= 1:  # Energy fits into storage
                self._soc = virtual_soc
            else:  # Energy does not fit into storage
                power = - (1 - soc) * capacity / time_delta_h * (1 / efficiency_charge)
                self._soc = 1
        else:  # Edge Case: applies only if power or capacity are 0
            power = 0

        return power

    def reset(self) -> None:
        """
        Resets the storage into its initial state.
        """
        self._soc = self._initial_soc

    def get_state(self) -> dict[str, float]:
        """
        Returns the state of charge.
        """
        return {
            'soc': self._soc,
        }

    @property
    def initial_soc(self) -> float:
        return self._initial_soc

    @property
    def eta_charge(self) -> float:
        return self._efficiency_charge

    @property
    def eta_discharge(self) -> float:
        return self._efficiency_discharge

    @property
    def time_delta_seconds(self) -> int:
        return self._time_delta_seconds

    @property
    def capacity(self) -> float:
        return self._capacity

    @capacity.setter
    def capacity(self, value: float) -> None:
        self._capacity = value

    @property
    def soc(self) -> float:
        return self._soc

    @property
    def label(self) -> str:
        return self._label
