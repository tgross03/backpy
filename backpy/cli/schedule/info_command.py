import rich_click as click
from rich.console import Console

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import BackupInput, BackupSpaceInput, print_error_message
from backpy.core.utils.exceptions import InvalidBackupError

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
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:

    verbose += 1

    return None
