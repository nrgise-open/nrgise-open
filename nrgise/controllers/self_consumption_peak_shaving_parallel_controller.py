from typing import Any, Dict, Tuple

from nrgise.common.state import State
from nrgise.components.storage.battery import Battery
from nrgise.controllers.controller_abc import ControllerABC
from nrgise.controllers.peak_shaving_controller import PeakShavingController
from nrgise.controllers.self_consumption_controller import SelfConsumptionController


class SelfConsumptionPeakShavingParallelController(ControllerABC):
    """
    Parallel multi application controller which performs self consumption and peak shaving.
    Each application uses a virtual battery, which limits the capacity and
    power usage per application (peak shaving or self consumption optimisation).
    See https://doi.org/10.1109/EEM.2019.8916568 and
    https://doi.org/10.1016/j.apenergy.2025.125353 for more details on the
    definition of paralell multi application controllers.
    The purpose of keeping track of the used energy per application using the virtual batteries is illustrated by the
    following example:

    If self consumption wants to charge and peak shaving wants to discharge. We don't want to do both actions on our
    physical storage. We can do both at once if we keep track of the energy which is reserved for which application.
    In the end, this saves us charge cycles on the physical battery.

    Args:
        storage_model: A model of the storage, so the virtual battery models can be derived from its parameters.
        cut_off_power_value: The *maximum* power value which should be reached
            by using peak shaving. See `PeakShavingController` for more
            details
        storage_label: Label of the storage to be controlled.
        power_share_peak_shaving: Share of storage power which is allocated for peak shaving in [0,1].
        capacity_share_peak_shaving: Share of storage capacity which is allocated for peak shaving in [0,1].
    """

    def __init__(
            self,
            storage_model: Battery,
            cut_off_power_value: float,
            storage_label: str,
            power_share_peak_shaving: float = 0.5,
            capacity_share_peak_shaving: float = 0.5,
    ):
        """
        Args:
            storage_model: the whole battery, on which parts are used for peak-shaving and self-consumption
            cut_off_power_value: Value at which peak shaving should be performed (see `PeakShavingController`).
            storage_label: name for storage
            power_share_peak_shaving: power used for peak-shaving
            capacity_share_peak_shaving: capacity used for peak-shaving
        """
        self._storage_label = storage_label
        self._self_consumption_controller = SelfConsumptionController(storage_label=storage_label)
        self._peak_shaving_controller = PeakShavingController(cut_off_power_value, storage_label=storage_label)

        self._power_share_peak_shaving = power_share_peak_shaving
        self._capacity_share_peak_shaving = capacity_share_peak_shaving

        self._virtual_peak_shaving_battery = Battery(
            label='virtual peak shaving battery',
            nom_power=storage_model.nom_power * self._power_share_peak_shaving,
            capacity=storage_model.capacity * self._capacity_share_peak_shaving,
            time_delta_seconds=storage_model.time_delta_seconds,
            initial_soc=storage_model.initial_soc,
            efficiency_charge=storage_model.eta_charge,
            efficiency_discharge=storage_model.eta_discharge,
        )
        self._virtual_self_consumption_battery = Battery(
            label='virtual self consumption battery',
            nom_power=storage_model.nom_power * (1 - self._power_share_peak_shaving),
            capacity=storage_model.capacity * (1 - self._capacity_share_peak_shaving),
            time_delta_seconds=storage_model.time_delta_seconds,
            initial_soc=storage_model.initial_soc,
            efficiency_charge=storage_model.eta_charge,
            efficiency_discharge=storage_model.eta_discharge,
        )

    def get_action(self, state: State) -> Tuple[Dict[str, float], Any]:
        # 1. Do self consumption optimisation using the virtual self consumption storage
        required_self_consumption_power, _ = self._self_consumption_controller.get_action(state)
        # Accessing 0 element as returned power is always an array
        self_consumption_power_applied = self._virtual_self_consumption_battery.set_power_contribution(
            sum(required_self_consumption_power.values()))

        # 2. Update State with the power fed into the grid from the virtual self consumption storage
        # Reminder: Negative self_consumption_power means charging aka. "loosing/consuming" power !!!
        virtual_state = State(
            uncontrolled_power_balance=state.uncontrolled_power_balance + self_consumption_power_applied,
            uncontrolled_power_contribution_per_component=None,  # type: ignore
            time_step=None,  # type: ignore
            components_states=None,  # type: ignore
            date_time=state.date_time,
        )

        # 3. Do Peak shaving using virtual peak shaving storge
        required_peak_shaving_power, _ = self._peak_shaving_controller.get_action(virtual_state)
        total_required_peak_shaving_power = sum(required_peak_shaving_power.values())
        peak_shaving_power_applied = self._virtual_peak_shaving_battery.set_power_contribution(
            total_required_peak_shaving_power)

        # 4. Calculate action for physical storage based on both virtual actions
        action = self_consumption_power_applied + peak_shaving_power_applied

        controller_state = {
            'virtual_self_consumption_battery_soc': self._virtual_self_consumption_battery.soc,
            'virtual_peak_shaving_battery_soc': self._virtual_peak_shaving_battery.soc,
        }
        return {self._storage_label: action}, controller_state
