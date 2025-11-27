import asyncio
import logging
import os
from enum import StrEnum

import click

from vm_stand_reaper.adapters.environment_variables import EnvironmentVariableName
from vm_stand_reaper.adapters.logging import setup_logging
from vm_stand_reaper.adapters.yc_settings import YCSettings
from vm_stand_reaper.service_layer import services


class CLIByTypeOption(StrEnum):
    VM = "vm"
    STAND = "stand"


setup_logging()
logger = logging.getLogger(__name__)


async def cleanup_outdated_stands() -> bool:
    """Delete all VMs that are outdated by VM Stand.

    Returns:
        True if all steps completed successfully, False otherwise
    """

    from vm_stand_reaper.service_layer import yc_uow

    uow = yc_uow.YCVirtualMachineUnitOfWork()

    try:
        logger.info("Starting analysis of Yandex Cloud")
        stands, not_in_vm_stands = await services.sort_vms_to_stands(uow)
        if not_in_vm_stands:
            logger.info("Cleanup VMs without required labels")
            await services.delete_vms(set(not_in_vm_stands), uow)
        if stands:
            logger.info("Cleanup outdated VM Stands")
            await services.delete_outdated_vm_stands(stands, uow)
        logger.info("Cleanup completed successfully")
        return True
    except Exception as e:
        logger.error("Cleanup failed: %s", e, exc_info=True)
        return False


async def cleanup_outdated_vms() -> bool:
    """Delete all VMs that are outdated concurrently.

    Returns:
        True if all steps completed successfully, False otherwise
    """

    from vm_stand_reaper.service_layer import yc_uow

    uow = yc_uow.YCVirtualMachineUnitOfWork()

    try:
        logger.info("Starting analysis of Yandex Cloud")
        await services.delete_outdated_vms(uow)
        logger.info("Cleanup completed successfully")
        return True
    except Exception as e:
        logger.error("Cleanup failed: %s", e, exc_info=True)
        return False


@click.command()
@click.option(
    "-b",
    "--by_type",
    default=CLIByTypeOption.VM.value,
    type=click.Choice([val.value for val in CLIByTypeOption]),
    help="How to delete VMs in the cloud. "
    f"'{CLIByTypeOption.STAND}' - sequentially by VM stand, '{CLIByTypeOption.VM}' - concurrently by VM",
)
@click.option(
    "-k",
    "--sa-key-path",
    type=click.STRING,
    envvar=EnvironmentVariableName.YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH,
    help="Path to the Yandex Cloud Service Account key JSON file. "
    f"Environment variable: {EnvironmentVariableName.YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH}",
)
@click.option(
    "-i",
    "--iam-token",
    type=click.STRING,
    envvar=EnvironmentVariableName.YANDEX_IAM_TOKEN,
    help="Yandex Cloud authentication token. "
    f"Environment variable: {EnvironmentVariableName.YANDEX_IAM_TOKEN}",
)
@click.option(
    "-a",
    "--oauth-token",
    type=click.STRING,
    envvar=EnvironmentVariableName.YANDEX_OAUTH_TOKEN,
    help="Yandex Cloud authorization token. "
    f"Environment variable: {EnvironmentVariableName.YANDEX_OAUTH_TOKEN}",
)
@click.option(
    "-c",
    "--cloud-id",
    type=click.STRING,
    envvar=EnvironmentVariableName.YANDEX_CLOUD_ID,
    help="ID of the cloud. "
    f"Environment variable: {EnvironmentVariableName.YANDEX_CLOUD_ID}",
)
@click.option(
    "-f",
    "--folder-id",
    type=click.STRING,
    envvar=EnvironmentVariableName.YANDEX_FOLDER_ID,
    help=f"ID of the folder in cloud. "
    f"Environment variable: {EnvironmentVariableName.YANDEX_FOLDER_ID}",
)
@click.option(
    "-t",
    "--ttl",
    type=click.STRING,
    envvar=EnvironmentVariableName.STAND_TTL,
    help=f"TTL(time to live) of the VM stand. "
    f"Environment variable: {EnvironmentVariableName.STAND_TTL}",
)
@click.pass_context
def cli(
    ctx: click.Context,
    by_type: str,
    sa_key_path: str,
    iam_token: str,
    oauth_token: str,
    cloud_id: str,
    folder_id: str,
    ttl: str,
) -> None:
    """A tool for removing unused VM Stands in the cloud.

    For usage set Environment variables or use CLI options
    """
    try:
        if iam_token:
            os.environ[EnvironmentVariableName.YANDEX_IAM_TOKEN] = iam_token
        if sa_key_path:
            os.environ[EnvironmentVariableName.YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH] = (
                sa_key_path
            )
        if oauth_token:
            os.environ[EnvironmentVariableName.YANDEX_OAUTH_TOKEN] = oauth_token
        if cloud_id:
            os.environ[EnvironmentVariableName.YANDEX_CLOUD_ID] = cloud_id
        if folder_id:
            os.environ[EnvironmentVariableName.YANDEX_FOLDER_ID] = folder_id
        if ttl:
            os.environ[EnvironmentVariableName.STAND_TTL] = ttl
        YCSettings.get_settings()
    except ValueError as exc:
        click.echo(f"Error: {exc}")
        click.echo()
        click.echo(ctx.get_help())
        ctx.exit(1)
    try:
        if by_type == CLIByTypeOption.STAND:
            cleanup_result = asyncio.run(cleanup_outdated_stands())
        else:
            cleanup_result = asyncio.run(cleanup_outdated_vms())
        if cleanup_result:
            click.echo("✅ Cleanup completed successfully")
        else:
            click.echo("❌ Cleanup completed with errors")
    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}")


if __name__ == "__main__":
    cli()
