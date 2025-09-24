from pathlib import Path

import click

from backpy import BackupSpaceType
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import DirectoryPathInput
from backpy.cli.space.common.create import common_options, create_backup_space

palette = get_default_palette()


def interactive() -> dict[str, Path]:
    return {
        "file_path": DirectoryPathInput(
            message="> Enter the directory you want to create backups of:"
        )
        .prompt()
        .expanduser()
    }


@click.command(
    "file_system",
    help=f"Create a backup space with a {palette.sky}'NAME'{RESET} for a "
    f"file system at a {palette.sky}'FILE_PATH'{RESET}.",
)
@common_options(space_type=BackupSpaceType.from_name("FILE_SYSTEM"))
@click.argument(
    "file_path",
    default="./",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def create_file_system(file_path: str, **kwargs) -> None:
    kwargs["file_path"] = file_path
    return create_backup_space(
        space_type="FILE_SYSTEM", interactive_func=interactive, **kwargs
    )
