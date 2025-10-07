import click
from rich.console import Console

from backpy import Backup, BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import BackupInput, BackupSpaceInput, print_error_message
from backpy.core.utils.exceptions import InvalidBackupError, InvalidBackupSpaceError

palette = get_default_palette()


def info_interactive(verbosity_level: int, debug: bool):
    space = BackupSpaceInput(suggest_matches=True).prompt()

    if len(space.get_backups(check_hash=False)) == 0:
        return print_error_message(
            InvalidBackupError("There is no Backup present in this Backup Space!"),
            debug=debug,
        )

    backup = BackupInput(
        backup_space=space,
        suggest_matches=True,
    ).prompt()

    Console().print(backup.get_info_table())

    return None


@click.command(
    "info",
    help=f"Get info about a {palette.sky}'BACKUP'{RESET} identified by its UUID or a "
    f"keyword ('latest', 'oldest' or 'largest', 'smallest') "
    f"from a {palette.sky}'BACKUP_SPACE'{RESET} identified by its UUID or name.",
)
@click.argument("backup_space", type=str, default=None, required=False)
@click.argument("backup", type=str, default=None, required=False)
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
    "--interactive",
    "-i",
    is_flag=True,
    help="Get information about a backup in interactive mode.",
)
def info(
    backup_space: str | None,
    backup: str | None,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:

    verbose += 1

    if interactive:
        return info_interactive(verbosity_level=verbose, debug=debug)

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
                        f"There is no Backup with that UUID in the Backup Space "
                        f"'{space.get_name()}'"
                    ),
                    debug=debug,
                )

    Console().print(backup.get_info_table())

    return None
