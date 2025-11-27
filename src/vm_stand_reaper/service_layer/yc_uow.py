from vm_stand_reaper.adapters import yc_repository
from vm_stand_reaper.adapters.yc_settings import YCSettings
from vm_stand_reaper.service_layer.unit_of_work import AbstractUnitOfWork

DEFAULT_SDK_FACTORY = yc_repository.YCSDKFactory.create()


class YCVirtualMachineUnitOfWork(AbstractUnitOfWork):
    """
    Compute Instance(Yandex Cloud) implementation of Unit of Work.

    Provides:
        - Yandex Cloud SDK configuration
        - VM management
    """

    def __init__(self, sdk_factory=DEFAULT_SDK_FACTORY):
        """
        Initializes a new instance of Unit of Work.

        Args:
            sdk_factory (callable, optional): Factory for creating
                an API entry-point object for Yandex Cloud
        """
        self._settings = YCSettings.get_settings()
        self._sdk_factory = sdk_factory

    async def __aenter__(self):
        """
        Enters the Unit of Work context manager.

        Returns:
            vms (YCVirtualMachineRepository): Current Unit of Work instance
        """
        self.sdk = self._sdk_factory
        self.vms = yc_repository.YCVirtualMachineRepository(
            self.sdk, str(self._settings.yandex_folder_id)
        )
        self.vms.max_concurrent_requests = self._settings.yandex_max_active_operations
        return self

    async def __aexit__(self, *args):
        """
        Exits the Unit of Work context manager.
        """
        await self.rollback()

    async def commit(self):
        """
        Commit is not required for Yandex Cloud SDK.
        """
        pass

    async def rollback(self):
        """
        Rollback is not supported by the Yandex Cloud SDK.
        """
        if self.sdk:
            pass
