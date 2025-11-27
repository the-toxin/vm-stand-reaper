import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum, auto
from typing import Optional

from vm_stand_reaper.adapters.environment_variables import EnvironmentVariableName


class VirtualMachineLabelTTLValue(StrEnum):
    NEVER = auto()


class VirtualMachineStandOSEnv(StrEnum):
    STAND_TTL = EnvironmentVariableName.STAND_TTL


@dataclass(frozen=True)
class VirtualMachineLabels:
    """A class to represent Virtual Machine model(VM) labels.

    Attributes:
        stand_id (str, optional): ID of the VM stand
        stand_team (str, optional): Owner team of the VM stand
        stand_owner (str, optional): Owner of the VM stand
        stand_ttl (str, optional): TTL(time to live) of the VM stand

    Methods:
        has_required_labels(): Verify if the required labels have values
    """

    stand_id: Optional[str] = None
    stand_team: Optional[str] = None
    stand_owner: Optional[str] = None
    stand_ttl: Optional[str] = None

    def has_required_labels(self) -> bool:
        """Verify if the required labels have values.

        Returns:
            True all labels have values, False otherwise
        """
        required_labels = (self.stand_id, self.stand_team, self.stand_owner)
        return all(value is not None for value in required_labels)


@dataclass(frozen=True)
class VirtualMachine:
    """A class to represent Virtual Machine(VM) model.

    Attributes:
        vm_id (str): ID of the VM
        vm_name (str): Name team of the VM
        vm_created_at (datetime): Creation date of the VM
        vm_labels (VirtualMachineLabels): Labels of the VM
    """

    vm_id: str
    vm_name: str
    vm_created_at: datetime
    vm_labels: VirtualMachineLabels


class VirtualMachineStand:
    """A class to represent Virtual Machine(VM) stand model.

    Attributes:
        stand_id (str): ID of the VM stand
        stand_team (str): Owner team of the VM stand
        stand_owner (str): Owner of the VM stand

    Properties:
        stand_created_at (datetime): Creation date of the VM
        stand_delete_at (datetime | None): Date when the VM stand
            should be automatically removed.
        stand_ttl (str): TTL(time to live) of the VM stand
        vms (set[VirtualMachine]): Set of VirtualMachine objects

    Methods:
        add_vm(): Add a VM to the stand
        can_add_vm(): Verify if the VM can be added to the stand
    """

    _DEFAULT_STAND_TTL = "4h"

    def __init__(
        self,
        stand_id: str,
        stand_team: str,
        stand_owner: str,
        stand_created_at: datetime,
    ) -> None:
        """Initialize VM stand model.

        Args:
            stand_id (str): ID of the VM stand
            stand_team (str): Owner team of the VM stand
            stand_owner (str): Owner of the VM stand
            stand_created_at (datetime): Creation date of the VM stand
        """
        self.stand_id = stand_id
        self.stand_team = stand_team
        self.stand_owner = stand_owner
        self._stand_created_at = stand_created_at
        self._stand_delete_at = None
        self._vms = set()
        self._stand_ttl_default = self._parse_ttl(
            os.getenv(VirtualMachineStandOSEnv.STAND_TTL, self._DEFAULT_STAND_TTL)
        )
        self._stand_ttl = self._stand_ttl_default

    @property
    def stand_created_at(self) -> datetime:
        """datetime: Creation date of the VM stand."""
        return self._stand_created_at

    @property
    def stand_delete_at(self) -> datetime | None:
        """datetime | None: Date when the VM stand should be automatically removed."""
        return self._stand_delete_at

    @property
    def stand_ttl(self) -> str:
        """str: TTL(time to live) of the VM stand."""
        return self._stand_ttl

    @property
    def vms(self) -> set[VirtualMachine]:
        """set[VirtualMachine]: Set of Virtual Machines."""
        return self._vms

    def add_vm(self, vm: VirtualMachine) -> None:
        """Add a VM to the stand.

        Args:
            vm (VirtualMachine): Virtual Machine object
        """
        if self.can_add_vm(vm):
            self._vms.add(vm)
            self._update_stand_created_at(vm)
            self._update_stand_ttl(vm)
            self._update_stand_delete_at()

    def can_add_vm(self, vm: VirtualMachine) -> bool:
        """Verify if the VM can be added to the stand.

        Args:
            vm (VirtualMachine): Virtual Machine object

        Returns:
            True if VM and VM labels equals, False otherwise
        """
        return (
            self.stand_id == vm.vm_labels.stand_id
            and self.stand_team == vm.vm_labels.stand_team
            and self.stand_owner == vm.vm_labels.stand_owner
        )

    def _update_stand_created_at(self, vm: VirtualMachine) -> None:
        """Update 'stand_created_at' property.

        Update 'stand_created_at' property if 'vm_created_at' value
            is greater then 'stand_created_at'

        Args:
            vm (VirtualMachine): Virtual Machine object
        """
        if vm.vm_created_at > self._stand_created_at:
            self._stand_created_at = vm.vm_created_at

    def _update_stand_delete_at(self) -> None:
        """Update 'stand_delete_at' property.

        Update 'stand_delete_at' property relative to the value of `stand_ttl`
        """
        if self._stand_ttl == VirtualMachineLabelTTLValue.NEVER:
            self._stand_delete_at = None
        else:
            ttl_in_minutes = self._get_ttl_in_minutes(self._stand_ttl)
            if ttl_in_minutes:
                self._stand_delete_at = self._stand_created_at + timedelta(
                    minutes=ttl_in_minutes
                )

    def _update_stand_ttl(self, vm: VirtualMachine) -> None:
        """Update 'stand_ttl' property.

        Update 'stand_ttl' property based on the value of the 'stand_ttl' VM label
            or the system default TTL value

        Args:
            vm (VirtualMachine): Virtual Machine object
        """
        if vm.vm_labels.stand_ttl is None:
            return
        # VM stand_ttl value must be in valid format
        try:
            self._get_ttl_in_minutes(vm.vm_labels.stand_ttl)
        except ValueError:
            return
        if self._stand_ttl == self._stand_ttl_default:
            self._stand_ttl = self._parse_ttl(vm.vm_labels.stand_ttl)
            return
        if self._stand_ttl == VirtualMachineLabelTTLValue.NEVER:
            return
        vm_ttl = self._parse_ttl(vm.vm_labels.stand_ttl)
        if vm_ttl == VirtualMachineLabelTTLValue.NEVER:
            self._stand_ttl = vm_ttl
        else:
            vm_ttl_in_minutes = self._get_ttl_in_minutes(vm_ttl)
            stand_ttl_in_minutes = self._get_ttl_in_minutes(self._stand_ttl)
            if (vm_ttl_in_minutes and stand_ttl_in_minutes) and (
                vm_ttl_in_minutes > stand_ttl_in_minutes
            ):
                self._stand_ttl = vm_ttl

    def _parse_ttl(self, ttl: str) -> str:
        """Get validated TTL value.

        Get TTL value in valid format

        Args:
            ttl (str): String with TTL value

        Returns:
            Valid TTL value, or system default TTL value
        """
        try:
            ttl_in_minutes = self._get_ttl_in_minutes(ttl)
        except ValueError:
            return self._DEFAULT_STAND_TTL
        if not ttl_in_minutes:
            return VirtualMachineLabelTTLValue.NEVER
        return ttl.lower()

    @staticmethod
    def _get_ttl_in_minutes(ttl: str) -> int | None:
        """Get TTL in minutes.

        Args:
            ttl (str): String with TTL value

        Returns:
            TTL in minutes if value is in valid format
                or None if TTL equals 'never'
        """
        if ttl == VirtualMachineLabelTTLValue.NEVER:
            return None
        ttl_pattern = re.compile(r"^(\d+)([mhd])$")
        match = ttl_pattern.match(ttl.lower())
        if not match:
            raise ValueError(
                f"Invalid TTL format: {ttl}. "
                f"Expected format: 5m, 2h, 1d or '{VirtualMachineLabelTTLValue.NEVER}'"
            )
        value = int(match.group(1))
        unit = match.group(2)
        if value <= 0:
            raise ValueError(
                f"Invalid TTL value: {ttl}. The TTL value must be positive"
            )
        conversions = {"m": 1, "h": 60, "d": 24 * 60}
        return value * conversions[unit]
