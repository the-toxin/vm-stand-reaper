import asyncio
import logging
from datetime import datetime, timezone

from vm_stand_reaper.domain import model
from vm_stand_reaper.service_layer.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)


async def sort_vms_to_stands(
    uow: AbstractUnitOfWork,
) -> tuple[list[model.VirtualMachineStand], list[model.VirtualMachine]]:
    """Get VMs sorted by VM Stands

    Sort VMs to list of stands and list of unsorted VMs

    Args:
        uow (AbstractUnitOfWork): Unit of Work interface
            for AbstractRepository

    Returns:
        List of VirtualMachineStand objects and
            list of VirtualMachine objects
    """
    vm_stands = {}
    not_in_vm_stands = []
    logger.info("Fetching VMs information")
    async with uow:
        all_vms = await uow.vms.list()
    logger.info("Fetching VMs information process has been completed")
    if not all_vms:
        return [], []
    logger.info("Sorting VMs to Stands")
    for vm in all_vms:
        vm_labels = vm.vm_labels
        if not vm_labels.has_required_labels():
            not_in_vm_stands.append(vm)
            continue
        stand_group_by = (
            vm_labels.stand_id,
            vm_labels.stand_team,
            vm_labels.stand_owner,
        )
        if not vm_stands.get(stand_group_by):
            vm_stands[stand_group_by] = model.VirtualMachineStand(
                stand_id=str(vm_labels.stand_id),
                stand_team=str(vm_labels.stand_team),
                stand_owner=str(vm_labels.stand_owner),
                stand_created_at=vm.vm_created_at,
            )
        vm_stands[stand_group_by].add_vm(vm)
    logger.info("Sorting VMs to Stands process has been completed")
    return list(vm_stands.values()), not_in_vm_stands


async def delete_vms(vms: set[model.VirtualMachine], uow: AbstractUnitOfWork) -> bool:
    """Delete virtual machines in repository

    Args:
        vms (set[VirtualMachine]): Set of VirtualMachine object
        uow (AbstractUnitOfWork): Unit of Work interface
            for AbstractRepository

    Returns:
        True if all VMs was deleted, False otherwise
    """
    if not vms:
        logger.info("No VMs to delete")
        return True
    is_completed_successfully = True
    async with uow:
        try:
            delete_tasks = []
            for vm in vms:
                logger.info(
                    "Deletion of VM '%s' started. Id: %s Name: %s",
                    vm.vm_name,
                    vm.vm_id,
                    vm.vm_name,
                )
                delete_tasks.append(uow.vms.delete(vm.vm_id))
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            vms_list = list(vms)
            for i, result in enumerate(results):
                vm = vms_list[i]
                if isinstance(result, Exception):
                    logger.error("Deletion of VM '%s' failed: %s", vm.vm_name, result)
                    is_completed_successfully = False
                else:
                    logger.info(
                        "Deletion of VM '%s' completed successfully. Id: %s Name: %s",
                        vm.vm_name,
                        vm.vm_id,
                        vm.vm_name,
                    )
            return is_completed_successfully
        except Exception as exc:
            logger.error("Deletion of VMs failed: %s", exc, exc_info=True)
            return False


async def delete_vm_stand(
    vm_stand: model.VirtualMachineStand, uow: AbstractUnitOfWork
) -> bool:
    """Delete virtual machines in repository by VM Stand

    Args:
        vm_stand (VirtualMachineStand): VirtualMachineStand object
        uow (AbstractUnitOfWork): Unit of Work interface
            for AbstractRepository

    Returns:
        True if all VMs was deleted, False otherwise
    """
    logger.info(
        "Deletion of VM Stand '%s' started. Id: %s Team: %s Owner: %s TTL: %s",
        vm_stand.stand_id,
        vm_stand.stand_id,
        vm_stand.stand_team,
        vm_stand.stand_owner,
        vm_stand.stand_ttl,
    )
    try:
        result = await delete_vms(vm_stand.vms, uow)
        if result:
            logger.info(
                "Deletion of VM Stand '%s' completed successfully. Id: %s Team: %s Owner: %s TTL: %s",
                vm_stand.stand_id,
                vm_stand.stand_id,
                vm_stand.stand_team,
                vm_stand.stand_owner,
                vm_stand.stand_ttl,
            )
        else:
            logger.warning(
                "Deletion of VM Stand '%s' completed with errors", vm_stand.stand_id
            )
        return result
    except Exception as exc:
        logger.error(
            "Deletion of VM Stand '%s' failed: %s",
            vm_stand.stand_id,
            exc,
            exc_info=True,
        )
        return False


async def delete_outdated_vm_stands(
    vm_stands: list[model.VirtualMachineStand], uow: AbstractUnitOfWork
) -> None:
    """Delete virtual machines in repository by "unused" VM Stands

    If the Stand is calculated as unused, Stand VMs will be deleted.

    Args:
        vm_stand (list[VirtualMachineStand]): List of VirtualMachineStand object
        uow (AbstractUnitOfWork): Unit of Work interface
            for AbstractRepository
    """
    if not vm_stands:
        return
    logger.info("Deleting unused VM Stands")
    current = datetime.now(timezone.utc)
    outdated_stands = [
        stand
        for stand in vm_stands
        if stand.stand_delete_at and stand.stand_delete_at <= current
    ]
    if not outdated_stands:
        logger.info("No outdated VM Stands found")
        return
    for stand in outdated_stands:
        await delete_vm_stand(stand, uow)
    logger.info("Deleting unused VM Stands process has been completed")


async def delete_outdated_vms(uow: AbstractUnitOfWork) -> None:
    """Delete "outdated" virtual machines in repository

    If a VM is classified as not Stand VM, it will be deleted.
    If the Stand is calculated as unused, Stand VMs will be deleted.

    Args:
        uow (AbstractUnitOfWork): Unit of Work interface
            for AbstractRepository
    """
    outdated_vms = set()
    current = datetime.now(timezone.utc)
    stands, not_in_vm_stands = await sort_vms_to_stands(uow)
    for vm in not_in_vm_stands:
        logger.info(
            "Found outdated VM '%s'. Id: %s Stand: %s Team: %s Owner: %s TTL: %s",
            vm.vm_name,
            vm.vm_id,
            vm.vm_labels.stand_id,
            vm.vm_labels.stand_team,
            vm.vm_labels.stand_owner,
            vm.vm_labels.stand_ttl,
        )
        outdated_vms.add(vm)
    outdated_stands = [
        stand
        for stand in stands
        if stand.stand_delete_at and stand.stand_delete_at <= current
    ]
    for stand in outdated_stands:
        for vm in stand.vms:
            logger.info(
                "Found outdated VM '%s'. Id: %s Stand: %s Team: %s Owner: %s TTL: %s",
                vm.vm_name,
                vm.vm_id,
                stand.stand_id,
                stand.stand_team,
                stand.stand_owner,
                stand.stand_ttl,
            )
            outdated_vms.add(vm)
    if not outdated_vms:
        return
    logger.info("Deleting outdated VMs")
    await delete_vms(outdated_vms, uow)
    logger.info("Deleting outdated VMs process has been completed")
