import rich_click as click
from rich.console import Console

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.core.space import BackupSpace
from backpy.core.utils.exceptions import InvalidBackupSpaceError

palette = get_default_palette()


@click.command(
    "info",
    help=f"Get info about a {palette.sky}'BACKUP_SPACE'{RESET} identified "
    f"by its UUID or name.",
)
@click.argument(
    "backup_space",
    type=str,
    required=True,
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
def info(backup_space: str, verbose: int, debug: bool) -> None:

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

    space = space.get_as_child_class()

    remote = space.get_remote()

    if remote is not None:
        with remote(context_verbosity=verbose, debug=debug):
            Console().print(space.get_info_table(verbosity_level=verbose))
    else:
        Console().print(space.get_info_table(verbosity_level=verbose))

    return None
