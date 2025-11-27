import asyncio
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

from vm_stand_reaper.adapters.repository import AbstractRepository
from vm_stand_reaper.adapters.yc_settings import YCSettings
from vm_stand_reaper.domain.model import VirtualMachine, VirtualMachineLabels

logger = logging.getLogger(__name__)


class InstanceLabelName(StrEnum):
    ID = auto()
    TEAM = auto()
    OWNER = auto()
    TTL = auto()


class YCVirtualMachineRepository(AbstractRepository):
    """A class to represent a virtual machine(VM) repository object in Yandex Cloud.

    Attributes:
        folder_id (str): ID of the folder in cloud

    Properties:
        list_page_size (int): Maximum number of results to return per page
            in a single list request.
        max_concurrent_requests (int): Limit of concurrent requests

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
    _DEFAULT_MAX_CONCURRENT_REQUESTS = 10

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
        self._request_semaphore = asyncio.Semaphore(
            self._DEFAULT_MAX_CONCURRENT_REQUESTS
        )

    @property
    def list_page_size(self) -> int:
        """int: The maximum number of results per page to return in one list request."""
        return self._list_page_size

    @list_page_size.setter
    def list_page_size(self, new_val: int) -> None:
        """Change the maximum number of results per page to return in one list request.

        Args:
            new_val (int): New value for the maximum number of results per page
        """
        if isinstance(new_val, int) and 0 <= new_val <= 1000:
            self._list_page_size = new_val
        else:
            logger.error(
                "Error while setting 'list_page_size' value. Value should be in range [0, 1000]. "
                "Using the default value %s",
                self._DEFAULT_LIST_PAGE_SIZE,
                exc_info=True,
            )
            self._list_page_size = self._DEFAULT_LIST_PAGE_SIZE

    @property
    def max_concurrent_requests(self) -> int:
        """int: The limit of concurrent requests."""
        return self._request_semaphore._value

    @max_concurrent_requests.setter
    def max_concurrent_requests(self, new_val: int) -> None:
        """Change the limit of concurrent requests.

        Args:
            new_val (int): New value for the limit of concurrent requests
        """
        self._request_semaphore = asyncio.Semaphore(new_val)

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

    async def get(self, vm_id: str) -> VirtualMachine:
        """Get VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            VirtualMachine object
        """
        try:
            async with self._request_semaphore:
                request = GetInstanceRequest(instance_id=vm_id)
                instance = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._instance_service.Get(request)
                )
            return self._to_domain_model(instance)
        except Exception as exc:
            logger.error("Error while getting VM: %s", exc, exc_info=True)
            raise

    async def list(self) -> List[VirtualMachine]:
        """Get VM list

        Returns:
            List of VirtualMachine objects
        """
        vms = []
        page_token = ""
        try:
            while True:
                async with self._request_semaphore:
                    request = ListInstancesRequest(
                        folder_id=self.folder_id,
                        page_size=self._list_page_size,
                        page_token=page_token,
                    )
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self._instance_service.List(request)
                    )
                vms.extend(
                    [self._to_domain_model(instance) for instance in response.instances]
                )
                if not response.next_page_token:
                    break
                page_token = response.next_page_token
            return vms
        except Exception as exc:
            logger.error("Error while getting list of VMs: %s", exc, exc_info=True)
            raise

    async def get_by_name(self, name: str) -> VirtualMachine:
        """Get VM by name

        Args:
            name (str): Virtual machine name

        Returns:
            VirtualMachine object

        Raises:
            ValueError: If the VM is not found
        """
        try:
            async with self._request_semaphore:
                request = ListInstancesRequest(
                    folder_id=self.folder_id, filter=f"name = '{name}'"
                )
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._instance_service.List(request)
                )
            if response.instances:
                return self._to_domain_model(response.instances[0])
            raise ValueError(f"The virtual machine '{name}' not found")
        except Exception as exc:
            logger.error("Error while getting VM: %s", exc, exc_info=True)
            raise

    async def delete(self, vm_id: str) -> bool:
        """Delete VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            True if the VM deletion operation succeeds
        """
        try:
            async with self._request_semaphore:
                request = DeleteInstanceRequest(instance_id=vm_id)
                operation = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._instance_service.Delete(request)
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._sdk.wait_operation_and_get_result(operation)
                )
            return True
        except Exception as exc:
            logger.error("Error while deleting VM: %s", exc, exc_info=True)
            raise

    async def start(self, vm_id: str) -> bool:
        """Start VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            True if the VM starts successfully
        """
        try:
            async with self._request_semaphore:
                request = StartInstanceRequest(instance_id=vm_id)
                operation = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._instance_service.Start(request)
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._sdk.wait_operation_and_get_result(operation)
                )
            return True
        except Exception as exc:
            logger.error("Error while starting VM: %s", exc, exc_info=True)
            raise

    async def stop(self, vm_id: str) -> bool:
        """Stop VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            True if the VM stops successfully
        """
        try:
            async with self._request_semaphore:
                request = StopInstanceRequest(instance_id=vm_id)
                operation = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._instance_service.Stop(request)
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._sdk.wait_operation_and_get_result(operation)
                )
            return True
        except Exception as exc:
            logger.error("Error while stopping VM: %s", exc, exc_info=True)
            raise

    async def restart(self, vm_id: str) -> bool:
        """Restart VM

        Args:
            vm_id (str): Virtual machine ID

        Returns:
            True if the VM restarts successfully
        """
        try:
            async with self._request_semaphore:
                request = RestartInstanceRequest(instance_id=vm_id)
                operation = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._instance_service.Restart(request)
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._sdk.wait_operation_and_get_result(operation)
                )
            return True
        except Exception as exc:
            logger.error("Error while restarting VM: %s", exc, exc_info=True)
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
        if settings.yandex_iam_token:
            return SDK(retry_policy=retry_policy, iam_token=settings.yandex_iam_token)
        if settings.yandex_service_account_key_json_path:
            try:
                with open(settings.yandex_service_account_key_json_path) as key_file:
                    return SDK(
                        retry_policy=retry_policy,
                        service_account_key=json.load(key_file),
                    )
            except Exception as exc:
                logger.error(
                    "Error while configuring Yandex Cloud SDK: %s", exc, exc_info=True
                )
                raise
        return SDK(retry_policy=retry_policy, token=settings.yandex_oauth_token)
