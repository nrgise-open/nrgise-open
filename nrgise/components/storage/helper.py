from nrgise.common.helper import convert_power_to_energy


def calc_equivalent_cycle(power: float, time_delta_seconds: int, energy_capacity: float) -> float:
    """
    This way of calculating the full equivalent cycles was defined in 10.1016/j.est.2022.105634 (We adapted it to work
    with energy capacity not charge capacity)

    Returns:
        Number of full equivalent cycles that the battery performed during this timestep
    """
    energy_change = convert_power_to_energy(abs(power), time_delta_seconds)
    # Energy Change cannot be greater than the capacity of the storage
    energy_change = min(energy_change, energy_capacity)
    return energy_change / (2 * energy_capacity)
