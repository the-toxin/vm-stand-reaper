import os

import click

import logging
from vm_stand_reaper.adapters.environment_variables import EnvironmentVariableName
from vm_stand_reaper.adapters.yc_settings import YCSettings
from vm_stand_reaper.adapters.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-k",
    "--sa-key-path",
    type=click.STRING,
    envvar=EnvironmentVariableName.YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH,
    help=f"Path to the Yandex Cloud Service Account key JSON file. "
    f"Environment variable: {EnvironmentVariableName.YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH}",
)
@click.option(
    "-a",
    "--oauth-token",
    type=click.STRING,
    envvar=EnvironmentVariableName.YANDEX_OAUTH_TOKEN,
    help=f"Yandex Cloud authorization token. "
    f"Environment variable: {EnvironmentVariableName.YANDEX_OAUTH_TOKEN}",
)
@click.option(
    "-c",
    "--cloud-id",
    type=click.STRING,
    envvar=EnvironmentVariableName.YANDEX_CLOUD_ID,
    help=f"ID of the cloud. "
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
    sa_key_path: str,
    oauth_token: str,
    cloud_id: str,
    folder_id: str,
    ttl: str,
) -> None:
    """A tool for removing unused VM Stands in the cloud.

    For usage set Environment variables or use CLI options
    """
    try:
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

    from vm_stand_reaper.service_layer import services, yc_uow

    logger.info("Starting analysis of Yandex Cloud")
    uow = yc_uow.YCVirtualMachineUnitOfWork()
    stands, not_in_vm_stands = services.sort_vms_to_stands(uow)
    if not_in_vm_stands:
        services.delete_vms(set(not_in_vm_stands), uow)
    if stands:
        services.delete_outdated_vm_stands(stands, uow)
    logger.info("Done")


if __name__ == "__main__":
    cli()
