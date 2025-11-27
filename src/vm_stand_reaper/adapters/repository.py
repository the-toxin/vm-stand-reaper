import abc

from vm_stand_reaper.domain.model import VirtualMachine


class AbstractRepository(abc.ABC):
    """A class to represent an abstract virtual machine repository.

    Methods:
        get(): Get virtual machine
        get_by_name(): Get virtual machine by name
        list(): List virtual machines
        delete(): Delete virtual machine
    """

    @abc.abstractmethod
    async def get(self, vm_id: str) -> VirtualMachine:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_name(self, vm_name: str) -> VirtualMachine:
        raise NotImplementedError

    @abc.abstractmethod
    async def list(self) -> list[VirtualMachine]:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, vm_id: str) -> bool:
        raise NotImplementedError
