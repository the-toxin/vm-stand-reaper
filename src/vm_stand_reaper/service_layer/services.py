import logging
from datetime import datetime, timezone

from vm_stand_reaper.domain import model
from vm_stand_reaper.service_layer import unit_of_work

logger = logging.getLogger(__name__)


def sort_vms_to_stands(
    uow: unit_of_work.AbstractUnitOfWork,
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
    with uow:
        all_vms = uow.vms.list()
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


def delete_vms(
    vms: set[model.VirtualMachine], uow: unit_of_work.AbstractUnitOfWork
) -> bool:
    """Delete virtual machines in repository

    Args:
        vms (set[VirtualMachine]): Set of VirtualMachine object
        uow (AbstractUnitOfWork): Unit of Work interface
            for AbstractRepository

    Returns:
        True if all VMs was deleted, False otherwise
    """
    with uow:
        try:
            for vm in vms:
                logger.info(
                    "Deletion of VM '%s' started. Id: %s Name: %s",
                    vm.vm_name,
                    vm.vm_id,
                    vm.vm_name,
                )
                uow.vms.delete(vm.vm_id)
                logger.info(
                    "Deletion of VM '%s' completed successfully. Id: %s Name: %s",
                    vm.vm_name,
                    vm.vm_id,
                    vm.vm_name,
                )
            return True
        except Exception as exc:
            logger.error("Deletion of VM '%s' failed: %s", vm.vm_name, exc)
            return False


def delete_vm_stand(
    vm_stand: model.VirtualMachineStand, uow: unit_of_work.AbstractUnitOfWork
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
        delete_vms(vm_stand.vms, uow)
        logger.info(
            "Deletion of VM Stand '%s' completed successfully. Id: %s Team: %s Owner: %s TTL: %s",
            vm_stand.stand_id,
            vm_stand.stand_id,
            vm_stand.stand_team,
            vm_stand.stand_owner,
            vm_stand.stand_ttl,
        )
        return True
    except Exception as exc:
        logger.error("Deletion of VM Stand '%s' failed: %s", vm_stand.stand_id, exc)
        return False


def delete_outdated_vm_stands(
    vm_stands: list[model.VirtualMachineStand], uow: unit_of_work.AbstractUnitOfWork
) -> None:
    """Delete virtual machines in repository by "unused" VM Stands

    If the Stand is calculated as unused, Stand VMs  will be deleted.

    Args:
        vm_stand (list[VirtualMachineStand]): List of VirtualMachineStand object
        uow (AbstractUnitOfWork): Unit of Work interface
            for AbstractRepository
    """
    if not vm_stands:
        return
    logger.info("Deleting unused VM Stands")
    current = datetime.now(timezone.utc)
    for vm_stand in vm_stands:
        if vm_stand.stand_delete_at is None:
            continue
        if vm_stand.stand_delete_at <= current:
            delete_vm_stand(vm_stand, uow)
    logger.info("Deleting unused VM Stands process has been completed")
