import rich_click as click
from rich.console import Console

from backpy import Backup, BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import (
    BackupInput,
    BackupSpaceInput,
    ConfirmInput,
    print_error_message,
)
from backpy.core.utils.exceptions import InvalidBackupError, InvalidBackupSpaceError

palette = get_default_palette()


def unlock_interactive(force: bool, debug: bool, verbosity_level: int):

    space = BackupSpaceInput(suggest_matches=True).prompt()

    if len(space.get_backups(check_hash=False)) == 0:
        return print_error_message(
            InvalidBackupError("There is no Backup present in this Backup Space!"),
            debug=debug,
        )

    backup = BackupInput(backup_space=space, suggest_matches=True).prompt()

    Console().print(backup.get_info_table(verbosity_level=verbosity_level))
    if not force:
        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to unlock backup "
            f"{palette.maroon}{str(backup.get_uuid())}{palette.base}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            backup.unlock(verbosity_level=verbosity_level)
        else:
            print(
                f"{palette.red}Canceled unlocking of backup "
                f"{palette.maroon}{str(backup.get_uuid())}{palette.red}.{RESET}"
            )
    else:
        backup.unlock(verbosity_level=verbosity_level)

    return None


@click.command(
    "unlock",
    help=f"Unlock a {palette.sky}'BACKUP'{RESET} identified by its UUID or a "
    f"keyword ('latest', 'oldest' or 'largest', 'smallest') "
    f"from a {palette.sky}'BACKUP_SPACE'{RESET} identified by its UUID or name. "
    f"An unlocked backup can be deleted automatically (e.g. if the backup space is full).",
)
@click.argument("backup_space", type=str, default=None, required=False)
@click.argument("backup", type=str, default=None, required=False)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the locking of the backup. This will skip the confirmation step.",
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
@click.option(
    "--interactive", "-i", is_flag=True, help="Lock the backup in interactive mode."
)
def unlock(
    backup_space: str | None,
    backup: str | None,
    force: bool,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:
    verbose += 1

    if interactive:
        return unlock_interactive(force=force, debug=debug, verbosity_level=verbose)

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

    space = space.get_as_child_class()

    if len(space.get_backups(check_hash=False)) == 0:
        return print_error_message(
            InvalidBackupError("There is no Backup present in this Backup Space!"),
            debug=debug,
        )

    match backup:
        case "oldest":
            backup = space.get_backups(sort_by="date", check_hash=False)[-1]
        case "newest":
            backup = space.get_backups(sort_by="date", check_hash=False)[0]
        case "largest":
            backup = space.get_backups(sort_by="size", check_hash=False)[0]
        case "smallest":
            backup = space.get_backups(sort_by="size", check_hash=False)[-1]
        case _:
            try:
                backup = Backup.load_by_uuid(
                    backup_space=space, unique_id=backup, verbosity_level=verbose
                )
            except Exception:
                return print_error_message(
                    InvalidBackupError(
                        f"There is no Backup with that UUID in the Backup "
                        f"Space '{space.get_name()}'"
                    ),
                    debug=debug,
                )

    if not backup.is_locked():
        return print_error_message(
            error=ValueError("This backup is not locked!"), debug=debug
        )

    Console().print(backup.get_info_table(verbosity_level=verbose))
    if not force:
        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to lock backup "
            f"{palette.maroon}{str(backup.get_uuid())}{palette.base}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            backup.unlock(verbosity_level=verbose)
        else:
            print(
                f"{palette.red}Canceled unlocking of backup "
                f"{palette.maroon}{str(backup.get_uuid())}{palette.red}.{RESET}"
            )
    else:
        backup.unlock(verbosity_level=verbose)

    return None
