from __future__ import annotations

import abc

from vm_stand_reaper.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    """Abstract interface for Unit of Work pattern.

    Defines contract for Unit of Work implementation in various contexts
    """

    vms: repository.AbstractRepository

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    @abc.abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self):
        raise NotImplementedError
