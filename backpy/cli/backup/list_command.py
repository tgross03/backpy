import rich_click as click
from rich.console import Console
from rich.tree import Tree

from backpy import BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.core.utils import format_bytes
from backpy.core.utils.exceptions import InvalidBackupSpaceError

palette = get_default_palette()


@click.command(
    "list",
    help=f"List all backups in a {palette.sky}'BACKUP_SPACE'{RESET} "
    f"identified by its UUID or name.",
)
@click.argument("backup_space", type=str, default=None, required=True)
@click.option(
    "--sort-by",
    "-s",
    type=click.Choice(["date", "size"]),
    default="date",
    help="The property to sort the backups by.",
)
@click.option(
    "--depth",
    type=int,
    default=1,
    help="The amount of details to show for each remote. Default is 1.",
)
@click.option(
    "--check-hash", is_flag=True, help="Whether to check the SHA256 hash of the file."
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
def list_backups(
    backup_space: str | None,
    sort_by: str,
    check_hash: bool,
    verbose: int,
    depth: int,
    debug: bool,
) -> None:

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

    tree = Tree(
        f"{palette.mauve}Backups in {palette.lavender}{space.get_name()} (UUID: {space.get_uuid()})"
        f"\n{palette.mauve}Sorted by: {palette.lavender}{sort_by}{RESET}"
    )

    try:
        backups = space.get_backups(sort_by=sort_by, check_hash=check_hash)
    except Exception as e:
        return print_error_message(error=e, debug=debug)

    for backup in backups:
        backup_branch = tree.add(
            f"{palette.sky}{backup.get_uuid()}{RESET}",
        )

        if check_hash:
            hash_branch = backup_branch.add(f"{palette.lavender}Hash Check{RESET}")
            if backup.has_local_archive():
                local_check = (
                    f"{palette.green}passed{RESET}"
                    if backup.check_hash(remote=False, verbosity_level=verbose)
                    else "failed"
                )
                hash_branch.add(
                    f"{palette.lavender}Local: {palette.maroon}" f"{local_check}{RESET}"
                )
            if backup.has_remote_archive() is not None:
                remote_check = (
                    f"{palette.green}passed{RESET}"
                    if backup.check_hash(remote=True, verbosity_level=verbose)
                    else "failed"
                )
                hash_branch.add(
                    f"{palette.lavender}Remote: {palette.maroon}"
                    f"{remote_check}{RESET}"
                )

        if depth > 1:
            backup_branch.add(
                f"{palette.lavender}Created at: "
                f"{palette.maroon}{backup.get_created_at().printformat()}{RESET}"
            )
            backup_branch.add(
                f"{palette.lavender}Size: "
                f"{palette.maroon}{format_bytes(backup.get_file_size())}{RESET}"
            )

        if depth > 2:
            comment = backup.get_comment() if backup.get_comment() != "" else "- none -"
            backup_branch.add(
                f"{palette.lavender}Comment: {palette.maroon}{comment}{RESET}"
            )

    Console().print(tree)

    return None
