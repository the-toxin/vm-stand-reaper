from datetime import datetime, timedelta, timezone

import pytest

from vm_stand_reaper.adapters import repository
from vm_stand_reaper.domain import model
from vm_stand_reaper.service_layer import services, unit_of_work

today = datetime.now(timezone.utc)


class FakeRepository(repository.AbstractRepository):
    def __init__(self, vms: list[model.VirtualMachine]):
        self._vms = set(vms)

    def add(self, vm):
        self._vms.add(vm)

    def get(self, vm_id: str):
        return next(vm for vm in self._vms if vm.vm_id == vm_id)

    def get_by_name(self, vm_name: str):
        return next(vm for vm in self._vms if vm.vm_name == vm_name)

    def list(self):
        return list(self._vms)

    def delete(self, vm_id: str):
        vm = self.get(vm_id)
        self._vms.remove(vm)
        return True


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self, vms: list[model.VirtualMachine]):
        self.vms = FakeRepository(vms)

    def __exit__(self, *args):
        pass


def get_today_hours_ago(h):
    return today - timedelta(hours=h)


def get_vm(
    naming_suffix="01",
    stand_ttl="2h",
    stand_naming_suffix="01",
    stand_team="pe_team",
    created_at=today,
    stand_owner: str | None = None,
):
    return model.VirtualMachine(
        f"vm-id-{naming_suffix}",
        f"vm-name-{naming_suffix}",
        created_at,
        model.VirtualMachineLabels(
            f"stand-{stand_naming_suffix}", stand_team, stand_owner, stand_ttl
        ),
    )


def get_vm_stand(
    naming_suffix="01", stand_team="pe_team", stand_owner="bender", created_at=today
):
    return model.VirtualMachineStand(
        f"stand-{naming_suffix}", stand_team, stand_owner, created_at
    )


@pytest.mark.parametrize(
    "vms, expected_stands, expected_not_in_stands",
    [
        (
            {
                "vm_01": {"stand_id": "01", "stand_owner": "bender"},
                "vm_02": {"stand_id": "01", "stand_owner": "bender"},
                "vm_03": {"stand_id": "02", "stand_owner": "bender"},
            },
            2,
            0,
        ),
        (
            {
                "vm_01": {"stand_id": "01", "stand_owner": None},
                "vm_02": {"stand_id": "01", "stand_owner": "bender"},
                "vm_03": {"stand_id": "02", "stand_owner": None},
            },
            1,
            2,
        ),
        (
            {
                "vm_01": {"stand_id": "01", "stand_owner": None},
                "vm_02": {"stand_id": "01", "stand_owner": None},
                "vm_03": {"stand_id": "02", "stand_owner": None},
            },
            0,
            3,
        ),
    ],
)
def test_sort_vms_to_stands(vms, expected_stands, expected_not_in_stands):
    vm_01 = get_vm(
        naming_suffix="01",
        stand_naming_suffix=vms["vm_01"]["stand_id"],
        stand_owner=vms["vm_01"]["stand_owner"],
    )
    vm_02 = get_vm(
        naming_suffix="02",
        stand_naming_suffix=vms["vm_02"]["stand_id"],
        stand_owner=vms["vm_02"]["stand_owner"],
    )
    vm_03 = get_vm(
        naming_suffix="03",
        stand_naming_suffix=vms["vm_03"]["stand_id"],
        stand_owner=vms["vm_03"]["stand_owner"],
    )
    uow = FakeUnitOfWork([vm for vm in {vm_01, vm_02, vm_03}])
    stands, not_in_vm_stands = services.sort_vms_to_stands(uow)
    assert len(stands) == expected_stands
    assert len(not_in_vm_stands) == expected_not_in_stands


def test_delete_vms():
    vm_01 = get_vm(naming_suffix="01")
    vm_02 = get_vm(naming_suffix="02")
    vms = {vm_01, vm_02}
    uow = FakeUnitOfWork([vm for vm in vms])
    services.delete_vms(vms, uow)
    assert uow.vms.list() == []


def test_delete_vm_stand():
    vm_01 = get_vm(naming_suffix="01", stand_naming_suffix="01", stand_owner="bender")
    vm_02 = get_vm(naming_suffix="02", stand_naming_suffix="02", stand_owner="bender")
    uow = FakeUnitOfWork([vm for vm in {vm_01, vm_02}])
    vm_stand_01 = get_vm_stand(naming_suffix="01", stand_owner="bender")
    vm_stand_01.add_vm(vm_01)
    services.delete_vm_stand(vm_stand_01, uow)
    assert uow.vms.list() == [vm_02]


@pytest.mark.parametrize(
    "vms, expected",
    [
        (
            {
                "vm_01": {
                    "stand_id": "01",
                    "stand_owner": "bender",
                    "created_hours_ago": "1",
                    "stand_ttl": "5m",
                },
                "vm_02": {
                    "stand_id": "02",
                    "stand_owner": "bender",
                    "created_hours_ago": "3",
                    "stand_ttl": "2h",
                },
            },
            0,
        ),
        (
            {
                "vm_01": {
                    "stand_id": "01",
                    "stand_owner": "bender",
                    "created_hours_ago": "1",
                    "stand_ttl": "never",
                },
                "vm_02": {
                    "stand_id": "02",
                    "stand_owner": "bender",
                    "created_hours_ago": "1",
                    "stand_ttl": "2h",
                },
            },
            2,
        ),
    ],
)
def test_delete_outdated_vm_stands(vms, expected):
    vm_01 = get_vm(
        naming_suffix="01",
        stand_naming_suffix=vms["vm_01"]["stand_id"],
        created_at=get_today_hours_ago(int(vms["vm_01"]["created_hours_ago"])),
        stand_owner=vms["vm_01"]["stand_owner"],
        stand_ttl=vms["vm_01"]["stand_ttl"],
    )
    vm_02 = get_vm(
        naming_suffix="02",
        stand_naming_suffix=vms["vm_02"]["stand_id"],
        created_at=get_today_hours_ago(int(vms["vm_01"]["created_hours_ago"])),
        stand_owner=vms["vm_02"]["stand_owner"],
        stand_ttl=vms["vm_01"]["stand_ttl"],
    )
    uow = FakeUnitOfWork([vm for vm in {vm_01, vm_02}])
    vm_stand_01 = get_vm_stand(
        naming_suffix=vms["vm_01"]["stand_id"],
        stand_owner=vms["vm_01"]["stand_owner"],
        created_at=get_today_hours_ago(int(vms["vm_01"]["created_hours_ago"])),
    )
    vm_stand_01.add_vm(vm_01)
    vm_stand_02 = get_vm_stand(
        naming_suffix=vms["vm_02"]["stand_id"],
        stand_owner=vms["vm_01"]["stand_owner"],
        created_at=get_today_hours_ago(int(vms["vm_01"]["created_hours_ago"])),
    )
    vm_stand_02.add_vm(vm_02)
    stands = [vm_stand_01, vm_stand_02]
    services.delete_outdated_vm_stands(stands, uow)
    assert len(uow.vms.list()) == expected
