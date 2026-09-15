from nrgise.components import Battery, StorageWrapperABC


class DummyWrapper(StorageWrapperABC):

    def get_state(self):
        pass

    def reset(self):
        pass

    def set_power_contribution(self, power: float) -> float:  # noqa
        self.capacity = self.capacity * 0.9
        return 0


def test_capacity_is_in_sync():
    storage = Battery(label='', nom_power=100, capacity=100, time_delta_seconds=3600,
                                           initial_soc=1)
    aging_storge = DummyWrapper(storage)
    aging_storge.set_power_contribution(10)

    assert aging_storge.capacity == aging_storge.storage.capacity


def test_storage_properties_can_be_accessed():
    storage = Battery(label='',
                                           nom_power=100,
                                           capacity=100,
                                           time_delta_seconds=3600,
                                           initial_soc=1,
                                           )
    aging_storge = DummyWrapper(storage)

    assert aging_storge.time_delta_seconds == 3600
