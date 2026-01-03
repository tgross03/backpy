from pathlib import Path

import rich_click as click

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import ConfirmInput
from backpy.cli.space.common.edit import common_options, edit_backup_space
from backpy.core.space import BackupSpaceType

palette = get_default_palette()


@click.command(
    "file_system",
    help=f"Edit a {palette.sky}'BACKUP_SPACE'{RESET} identified by its name or UUID.",
)
@click.option(
    "--file-path",
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="The path to the directory that should be backed up.",
)
@common_options(space_type=BackupSpaceType.FILE_SYSTEM)
def edit_file_system(file_path: str | None, **kwargs) -> None:

    force = kwargs["force"]
    additional_values = dict()

    if file_path is not None:

        path = Path(file_path).resolve()

        confirm = False or force

        if not force:
            confirm = ConfirmInput(
                message=f"> Are you sure you want to change the remote of this backup space to "
                f"{palette.sky}{path}{RESET}",
                default_value=False,
            ).prompt()

        if confirm:
            additional_values["_file_path"] = path
        else:
            print(
                f"{palette.maroon}File path change canceled. "
                f"All other changes will be applied{RESET}"
            )

    return edit_backup_space(additional_values=additional_values, **kwargs)
