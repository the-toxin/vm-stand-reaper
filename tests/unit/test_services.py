import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from vm_stand_reaper.adapters import repository
from vm_stand_reaper.domain import model
from vm_stand_reaper.service_layer import services, unit_of_work

today = datetime.now(timezone.utc)


class FakeRepository(repository.AbstractRepository):
    def __init__(self, vms: list[model.VirtualMachine]):
        self._vms = set(vms)

    async def add(self, vm):
        self._vms.add(vm)

    async def get(self, vm_id: str):
        return next(vm for vm in self._vms if vm.vm_id == vm_id)

    async def get_by_name(self, vm_name: str):
        return next(vm for vm in self._vms if vm.vm_name == vm_name)

    async def list(self):
        await asyncio.sleep(0.01)
        return list(self._vms)

    async def delete(self, vm_id: str):
        vm = await self.get(vm_id)
        self._vms.remove(vm)
        await asyncio.sleep(0.01)
        return True


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self, vms: list[model.VirtualMachine]):
        self.vms = FakeRepository(vms)
        self._committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    async def commit(self):
        self._committed = True
        await asyncio.sleep(0.01)

    async def rollback(self):
        await asyncio.sleep(0.01)


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
async def test_sort_vms_to_stands(vms, expected_stands, expected_not_in_stands):
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
    stands, not_in_vm_stands = await services.sort_vms_to_stands(uow)
    assert len(stands) == expected_stands
    assert len(not_in_vm_stands) == expected_not_in_stands


async def test_delete_vms():
    vm_01 = get_vm(naming_suffix="01")
    vm_02 = get_vm(naming_suffix="02")
    vms = {vm_01, vm_02}
    uow = FakeUnitOfWork([vm for vm in vms])
    await services.delete_vms(vms, uow)
    assert await uow.vms.list() == []


async def test_delete_vm_stand():
    vm_01 = get_vm(naming_suffix="01", stand_naming_suffix="01", stand_owner="bender")
    vm_02 = get_vm(naming_suffix="02", stand_naming_suffix="02", stand_owner="bender")
    uow = FakeUnitOfWork([vm for vm in {vm_01, vm_02}])
    vm_stand_01 = get_vm_stand(naming_suffix="01", stand_owner="bender")
    vm_stand_01.add_vm(vm_01)
    await services.delete_vm_stand(vm_stand_01, uow)
    assert await uow.vms.list() == [vm_02]


@pytest.mark.parametrize(
    "vms, expected",
    [
        (
            {
                "vm_01": {
                    "stand_id": "01",
                    "stand_owner": "bender",
                    "stand_ttl": "5m",
                    "created_hours_ago": "1",
                },
                "vm_02": {
                    "stand_id": "02",
                    "stand_owner": "bender",
                    "stand_ttl": "2h",
                    "created_hours_ago": "3",
                },
            },
            0,
        ),
        (
            {
                "vm_01": {
                    "stand_id": "01",
                    "stand_owner": "bender",
                    "stand_ttl": "never",
                    "created_hours_ago": "1",
                },
                "vm_02": {
                    "stand_id": "02",
                    "stand_owner": "bender",
                    "stand_ttl": "2h",
                    "created_hours_ago": "1",
                },
            },
            2,
        ),
    ],
)
async def test_delete_outdated_vm_stands(vms, expected):
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
        created_at=get_today_hours_ago(int(vms["vm_02"]["created_hours_ago"])),
        stand_owner=vms["vm_02"]["stand_owner"],
        stand_ttl=vms["vm_02"]["stand_ttl"],
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
        stand_owner=vms["vm_02"]["stand_owner"],
        created_at=get_today_hours_ago(int(vms["vm_02"]["created_hours_ago"])),
    )
    vm_stand_02.add_vm(vm_02)
    stands = [vm_stand_01, vm_stand_02]
    await services.delete_outdated_vm_stands(stands, uow)
    assert len(await uow.vms.list()) == expected



@pytest.mark.parametrize(
    "vms, expected",
    [
        (
            {
                "vm_01": {
                    "stand_id": "01",
                    "stand_owner": None,
                    "stand_ttl": None,
                    "created_hours_ago": "1",
                },
                "vm_02": {
                    "stand_id": "02",
                    "stand_owner": "bender",
                    "stand_ttl": "1h",
                    "created_hours_ago": "2",
                },
            },
            0,
        ),
        (
            {
                "vm_01": {
                    "stand_id": "02",
                    "stand_owner": None,
                    "stand_ttl": None,
                    "created_hours_ago": "1",
                },
                "vm_02": {
                    "stand_id": "02",
                    "stand_owner": "bender",
                    "stand_ttl": "5h",
                    "created_hours_ago": "never",
                },
            },
            1,
        ),
    ],
)
async def test_delete_outdated_vms(vms, expected):
    vm_01 = get_vm(
        naming_suffix="01",
        stand_naming_suffix=vms["vm_01"]["stand_id"],
        stand_owner=vms["vm_01"]["stand_owner"],
        stand_ttl=vms["vm_01"]["stand_ttl"],
        created_at=get_today_hours_ago(int(vms["vm_01"]["created_hours_ago"])),
    )
    vm_02 = get_vm(
        naming_suffix="02",
        stand_naming_suffix=vms["vm_02"]["stand_id"],
        stand_owner=vms["vm_02"]["stand_owner"],
        stand_ttl=vms["vm_02"]["stand_ttl"],
        created_at=get_today_hours_ago(int(vms["vm_01"]["created_hours_ago"])),
    )
    uow = FakeUnitOfWork([vm for vm in {vm_01, vm_02}])
    s, nos = await services.sort_vms_to_stands(uow)
    print(s)
    await services.delete_outdated_vms(uow)
    assert len(await uow.vms.list()) == expected
