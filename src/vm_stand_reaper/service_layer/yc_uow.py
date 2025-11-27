from vm_stand_reaper.adapters import repository
from vm_stand_reaper.adapters.yc_settings import YCSettings
from vm_stand_reaper.service_layer.unit_of_work import AbstractUnitOfWork

DEFAULT_SDK_FACTORY = repository.YCSDKFactory.create()


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
        self.yandex_folder_id = YCSettings.get_settings().yandex_folder_id
        self.sdk_factory = sdk_factory

    def __enter__(self):
        """
        Enters the Unit of Work context manager.

        Returns:
            vms (YCVirtualMachineRepository): Current Unit of Work instance
        """
        self.sdk = self.sdk_factory
        self.vms = repository.YCVirtualMachineRepository(
            self.sdk, str(self.yandex_folder_id)
        )
        return super().__enter__()

    def __exit__(self, *args):
        """
        Exits the Unit of Work context manager.
        """
        pass
