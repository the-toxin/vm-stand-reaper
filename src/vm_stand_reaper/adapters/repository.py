import abc
import datetime
import json
import logging
from enum import StrEnum, auto
from typing import List

import grpc
from google.protobuf.json_format import MessageToDict
from yandex.cloud.compute.v1.instance_pb2 import Instance
from yandex.cloud.compute.v1.instance_service_pb2 import (
    DeleteInstanceRequest,
    GetInstanceRequest,
    ListInstancesRequest,
    RestartInstanceRequest,
    StartInstanceRequest,
    StopInstanceRequest,
)
from yandex.cloud.compute.v1.instance_service_pb2_grpc import InstanceServiceStub
from yandexcloud._retry_policy import RetryPolicy
from yandexcloud._sdk import SDK

from vm_stand_reaper.adapters.yc_settings import YCSettings
from vm_stand_reaper.domain.model import VirtualMachine, VirtualMachineLabels

logger = logging.getLogger(__name__)


class AbstractRepository(abc.ABC):
    """A class to represent an abstract virtual machine repository.

    Methods:
        get(): Get virtual machine
        get_by_name(): Get virtual machine by name
        list(): List virtual machines
        delete(): Delete virtual machine
    """

    @abc.abstractmethod
    def get(self, vm_id: str) -> VirtualMachine:
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_name(self, vm_id: str) -> VirtualMachine:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[VirtualMachine]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, vm_id: str) -> bool:
        raise NotImplementedError


class InstanceLabelName(StrEnum):
    ID = auto()
    TEAM = auto()
    OWNER = auto()
    TTL = auto()


class YCVirtualMachineRepository(AbstractRepository):
    """A class to represent a virtual machine(VM) repository object in Yandex Cloud.

    Attributes:
        folder_id (str): ID of the folder in cloud

    Methods:
        get(): Get virtual machine
        list(): Get virtual machine list
        get_by_name(): Get virtual machine by name
        delete(): Delete virtual machine
        start(): Start virtual machine
        stop(): Stop virtual machine
        restart(): Restart virtual machine
    """

    _DEFAULT_LIST_PAGE_SIZE = 0

    def __init__(self, sdk: SDK, folder_id: str) -> None:
        """Initialize VM repository.

        Args:
            sdk (SDK): yandexcloud.SDK object
            folder_id (str): ID of the folder in cloud
        """
        self.folder_id = folder_id
        self._sdk = sdk
        self._instance_service = self._sdk.client(InstanceServiceStub)
        self._list_page_size = self._DEFAULT_LIST_PAGE_SIZE

    @property
    def list_page_size(self) -> int:
        """int: The maximum number of results per page to return in one list request."""
        return self._list_page_size

    @list_page_size.setter
    def list_page_size(self, new_val: int) -> None:
        """int: Set the maximum number of results per page to return in one list request."""
        if isinstance(new_val, int) and 0 <= new_val <= 1000:
            self._list_page_size = new_val
        logger.error(
            "Error while setting 'list_page_size' value. Value should be in range [0, 1000]. "
            "Using the default value %s", self._DEFAULT_LIST_PAGE_SIZE,
        )
        self._list_page_size = self._DEFAULT_LIST_PAGE_SIZE

    def _to_domain_model(self, instance: Instance) -> VirtualMachine:
        """Converts an Instance resource(Yandex Cloud) to a VirtualMachine model.

        Args:
            instance (yandex.cloud.compute.v1.instance_pb2.Instance):
                Instance object(Yandex Cloud)

        Returns:
            VirtualMachine object
        """
        instance_dict = MessageToDict(instance)
        created_at = datetime.datetime.fromisoformat(
            instance_dict.get("createdAt").replace("Z", "+00:00")  # type: ignore
        )
        instance_labels = instance_dict.get("labels", {})
        labels = VirtualMachineLabels(
            stand_id=instance_labels.setdefault(InstanceLabelName.ID, None),
            stand_team=instance_labels.setdefault(InstanceLabelName.TEAM, None),
            stand_owner=instance_labels.setdefault(InstanceLabelName.OWNER, None),
            stand_ttl=instance_labels.setdefault(InstanceLabelName.TTL, None),
        )
        return VirtualMachine(
            vm_id=instance.id,
            vm_name=instance.name,
            vm_created_at=created_at,
            vm_labels=labels,
        )

    def get(self, vm_id: str) -> VirtualMachine:
        """Get VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            VirtualMachine object
        """
        try:
            request = GetInstanceRequest(instance_id=vm_id)
            instance = self._instance_service.Get(request)
            return self._to_domain_model(instance)
        except Exception as exc:
            logger.error("Error while getting VM: %s", exc)
            raise

    def list(self) -> List[VirtualMachine]:
        """Get VM list

        Returns:
            List of VirtualMachine objects
        """
        vms = []
        page_token = ""
        try:
            while True:
                request = ListInstancesRequest(
                    folder_id=self.folder_id,
                    page_size=self._list_page_size,
                    page_token=page_token,
                )
                response = self._instance_service.List(request)
                vms.extend(
                    [self._to_domain_model(instance) for instance in response.instances]
                )
                if not response.next_page_token:
                    break
                page_token = response.next_page_token
            return vms
        except Exception as exc:
            logger.error("Error while getting list of VMs: %s", exc)
            raise

    def get_by_name(self, name: str) -> VirtualMachine:
        """Get VM by name

        Args:
            name (str): Virtual machine name

        Returns:
            VirtualMachine object

        Raises:
            ValueError: If the VM is not found
        """
        try:
            request = ListInstancesRequest(
                folder_id=self.folder_id, filter=f"name = '{name}'"
            )
            response = self._instance_service.List(request)
            if response.instances:
                return self._to_domain_model(response.instances[0])
            raise ValueError(f"The virtual machine '{name}' not found")
        except Exception as exc:
            logger.error("Error while getting VM: %s", exc)
            raise

    def delete(self, vm_id: str) -> bool:
        """Delete VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            True if the VM deletion operation succeeds
        """
        try:
            request = DeleteInstanceRequest(instance_id=vm_id)
            operation = self._instance_service.Delete(request)
            self._sdk.wait_operation_and_get_result(operation)
            return True
        except Exception as exc:
            logger.error("Error while deleting VM: %s", exc)
            raise

    def start(self, vm_id: str) -> bool:
        """Start VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            True if the VM starts successfully
        """
        try:
            request = StartInstanceRequest(instance_id=vm_id)
            operation = self._instance_service.Start(request)
            self._sdk.wait_operation_and_get_result(operation)
            return True
        except Exception as exc:
            logger.error("Error while starting VM: %s", exc)
            raise

    def stop(self, vm_id: str) -> bool:
        """Stop VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            True if the VM stops successfully
        """
        try:
            request = StopInstanceRequest(instance_id=vm_id)
            operation = self._instance_service.Stop(request)
            self._sdk.wait_operation_and_get_result(operation)
            return True
        except Exception as exc:
            logger.error("Error while stopping VM: %s", exc)
            raise

    def restart(self, vm_id: str) -> bool:
        """Restart VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            True if the VM restarts successfully
        """
        try:
            request = RestartInstanceRequest(instance_id=vm_id)
            operation = self._instance_service.Restart(request)
            self._sdk.wait_operation_and_get_result(operation)
            return True
        except Exception as exc:
            logger.error("Error while restarting VM: %s", exc)
            raise


class YCSDKFactory:
    """A class to represent a factory for creating an API entry-point object for Yandex Cloud.

    The factory for creating a virtual machine(VM) repository on Yandex Cloud

    Methods:
        create(): Create an API entry-point object
    """

    @staticmethod
    def create() -> SDK:
        """Create an API entry-point object for Yandex Cloud.

        Required settings will be obtained from environment variables such as YANDEX_*

        Returns:
            yandexcloud.SDK object
        """
        settings = YCSettings.get_settings()
        retry_policy = RetryPolicy(
            max_attempts=5, status_codes=(grpc.StatusCode.UNAVAILABLE,)
        )
        if settings.yandex_service_account_key_json_path:
            try:
                with open(settings.yandex_service_account_key_json_path) as key_file:
                    return SDK(
                        retry_policy=retry_policy,
                        service_account_key=json.load(key_file),
                    )
            except Exception as exc:
                logger.error("Error while configuring Yandex Cloud SDK: %s", exc)
                raise
        else:
            return SDK(retry_policy=retry_policy, token=settings.yandex_oauth_token)
