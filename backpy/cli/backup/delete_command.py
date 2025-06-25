import click

from backpy import Backup, BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import (
    BackupInput,
    BackupSpaceInput,
    ConfirmInput,
    print_error_message,
)
from backpy.exceptions import InvalidBackupError, InvalidBackupSpaceError

palette = get_default_palette()


def delete_interactive(verbosity_level: int):

    space = BackupSpaceInput(suggest_matches=True).prompt()
    backup = BackupInput(backup_space=space, suggest_matches=True).prompt()

    print(space.get_config())
    print(backup.get_config())


@click.command(
    "delete",
    help=f"Delete a {palette.sky}'BACKUP'{RESET} identified by its UUID or a "
    f"keyword ('latest' or 'oldest') "
    f"from a {palette.sky}'BACKUP_SPACE'{RESET} identified by its UUID or name.",
)
@click.argument("backup_space", type=str, default=None, required=False)
@click.argument("backup", type=str, default=None, required=False)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the deletion of the backup. This will skip the confirmation step.",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    default=1,
    help="Sets the verbosity level of the output.",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Activate the debug log for the command or interactive "
    "mode to print full error traces in case of a problem.",
)
@click.option(
    "--interactive", "-i", is_flag=True, help="Delete the backup in interactive mode."
)
def delete(
    backup_space: str | None,
    backup: str | None,
    force: bool,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:

    if interactive:
        return delete_interactive(verbosity_level=verbose)

    if backup_space is None or backup is None:
        return print_error_message(
            ValueError(
                "If the '--interactive' flag is not given, you have to supply "
                "a valid value for the 'BACKUP_SPACE' and 'BACKUP' arguments."
            ),
            debug=debug,
        )

    try:
        space = BackupSpace.load_by_uuid(backup_space)
    except Exception:
        try:
            space = BackupSpace.load_by_name(backup_space)
        except Exception:
            return print_error_message(
                InvalidBackupSpaceError(
                    "There is no Backup Space with that name or UUID!"
                ),
                debug=debug,
            )

    space = space.get_type().child_class.load_by_uuid(unique_id=str(space.get_uuid()))

    try:
        backup = Backup.load_by_uuid(
            backup_space=space, unique_id=backup, verbosity_level=verbose
        )
    except Exception:
        return print_error_message(
            InvalidBackupError(
                f"There is no Backup with that UUID in the Backup Space '{space.get_name()}'"
            ),
            debug=debug,
        )

    if not force:
        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to delete backup "
            f"{palette.maroon}{str(backup.get_uuid())}{palette.base}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            backup.delete(verbosity_level=verbose)
        else:
            print(
                f"{palette.red}Canceled removal of backup "
                f"{palette.maroon}{str(backup.get_uuid())}{palette.red}.{RESET}"
            )
    else:
        backup.delete(verbosity_level=verbose)

    return None
