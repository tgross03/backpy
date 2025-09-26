import click

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import ConfirmInput, print_error_message
from backpy.core.backup import BackupSpace
from backpy.core.utils.exceptions import InvalidBackupSpaceError

palette = get_default_palette()


@click.command(
    "delete",
    help=f"Delete a {palette.sky}'BACKUP_SPACE'{RESET} identified "
    f"by its UUID or name.",
)
@click.argument(
    "backup_space",
    type=str,
    required=True,
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the deletion. This will skip the confirmation step.",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Sets the verbosity level of the output.",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Activate the debug log for the command or interactive "
    "mode to print full error traces in case of a problem.",
)
def delete(backup_space: str, force: bool, verbose: bool, debug: bool) -> None:

    verbose += 1

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

    confirm = False or force

    if not force:
        confirm = ConfirmInput(
            message=f"> Are you sure you want to delete the backup space "
            f"{palette.sky}{space.get_name()} "
            f"(UUID: {space.get_uuid()}){RESET}?\n{palette.red}WARNING! "
            f"{palette.maroon}This cannot be undone and will remove every backup "
            f"of this space "
            f"{'(also from its remote)' if space.get_remote() is not None else ''}!{RESET}",
            default_value=False,
        ).prompt()

    if confirm:
        try:
            space.delete(verbosity_level=verbose)
        except Exception as e:
            return print_error_message(
                error=e,
                debug=debug,
            )
    else:
        print(f"{palette.maroon}Deletion canceled.{RESET}")

    return None
