import os
from datetime import datetime, timedelta

import pytest

from vm_stand_reaper.domain.model import (
    VirtualMachine,
    VirtualMachineLabels,
    VirtualMachineLabelTTLValue,
    VirtualMachineStand,
    VirtualMachineStandOSEnv,
)

today = datetime.now()
today_hour_ago = today - timedelta(hours=1)


def get_vm(naming_suffix="01", stand_ttl="2h"):
    return VirtualMachine(
        f"vm-id-{naming_suffix}",
        f"vm-name-{naming_suffix}",
        today,
        VirtualMachineLabels("stand-01", "pe_team", "bender", stand_ttl),
    )


def get_vm_stand(naming_suffix="01"):
    return VirtualMachineStand(f"stand-{naming_suffix}", "pe_team", "bender", today)


class TestVirtualMachineStand:
    """VirtualMachineStand base class tests"""

    def test_adding_vm_to_a_stand_increase_the_vms_count(self):
        vm_stand = get_vm_stand()
        vm_stand.add_vm(get_vm())
        assert len(vm_stand.vms) == 1

    def test_can_add_vm_if_required_labels_is_equal(self):
        vm_stand = get_vm_stand()
        assert vm_stand.can_add_vm(get_vm())

    def test_cannot_add_vm_if_required_labels_not_equal(self):
        vm_stand = VirtualMachineStand("stand-02", "pe_team", "bender", today)
        assert vm_stand.can_add_vm(get_vm()) is False

    def test_update_created_at_if_adding_later_created_vm(self):
        vm_stand = VirtualMachineStand("stand-01", "pe_team", "bender", today_hour_ago)
        vm_stand.add_vm(get_vm())
        assert vm_stand.stand_created_at == today


class TestVirtualMachineStandTTL:
    """VirtualMachineStand 'stand_ttl' property class tests"""

    @pytest.mark.parametrize("vm_stand_ttl", ["111m", "222h", "333d", "never"])
    def test_adding_vm_is_changing_stand_ttl(self, vm_stand_ttl):
        vm_stand = get_vm_stand()
        vm_stand.add_vm(get_vm(stand_ttl=vm_stand_ttl))
        assert vm_stand.stand_ttl == vm_stand_ttl

    def test_adding_vm_with_invalid_ttl_value_does_not_change_stand_ttl(self):
        vm_stand = get_vm_stand()
        stand_ttl = vm_stand.stand_ttl
        vm_stand.add_vm(get_vm(stand_ttl="?"))
        assert vm_stand.stand_ttl == stand_ttl

    def test_setting_stand_ttl_from_os_env(self):
        stand_ttl = "101m"
        os.environ[VirtualMachineStandOSEnv.STAND_TTL] = stand_ttl
        vm_stand = get_vm_stand()
        os.environ.pop(VirtualMachineStandOSEnv.STAND_TTL)
        assert vm_stand.stand_ttl == stand_ttl

    def test_stand_ttl_value_is_equal_the_highest_stand_ttl_in_vms(self):
        vm_stand = get_vm_stand()
        vm_stand_ttl = "never"
        vm_stand.add_vm(get_vm(naming_suffix="01", stand_ttl="20m"))
        vm_stand.add_vm(get_vm(naming_suffix="02", stand_ttl=vm_stand_ttl))
        vm_stand.add_vm(get_vm(naming_suffix="03", stand_ttl="30h"))
        assert vm_stand.stand_ttl == vm_stand_ttl


class TestVirtualMachineStandDeleteAt:
    """VirtualMachineStand 'stand_delete_at' property class tests"""

    @pytest.mark.parametrize(
        "vm_1_stand_ttl, vm_2_stand_ttl, vm_3_stand_ttl, max_ttl_in_minutes",
        [
            ("10m", "20h", "30d", 30 * 24 * 60),
            ("100m", "1h", "10m", 100),
            ("3h", VirtualMachineLabelTTLValue.NEVER, "100d", None),
        ],
    )
    def test_adding_vm_is_changing_stand_delete_at(
        self, vm_1_stand_ttl, vm_2_stand_ttl, vm_3_stand_ttl, max_ttl_in_minutes
    ):
        vm_stand = get_vm_stand()
        vm_stand.add_vm(get_vm(naming_suffix="01", stand_ttl=vm_1_stand_ttl))
        vm_stand.add_vm(get_vm(naming_suffix="02", stand_ttl=vm_2_stand_ttl))
        vm_stand.add_vm(get_vm(naming_suffix="03", stand_ttl=vm_3_stand_ttl))
        if max_ttl_in_minutes is None:
            stand_delete_at = None
        elif max_ttl_in_minutes == VirtualMachineLabelTTLValue.NEVER:
            stand_delete_at = VirtualMachineLabelTTLValue.NEVER
        else:
            stand_delete_at = today + timedelta(minutes=max_ttl_in_minutes)
        assert vm_stand.stand_delete_at == stand_delete_at
