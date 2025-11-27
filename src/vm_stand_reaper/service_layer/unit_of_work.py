from __future__ import annotations

import abc

from vm_stand_reaper.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    """Abstract interface for Unit of Work pattern.

    Defines contract for Unit of Work implementation in various contexts
    """

    vms: repository.AbstractRepository

    def __enter__(self) -> AbstractUnitOfWork:
        return self

    def __exit__(self, *args):
        raise NotImplementedError
