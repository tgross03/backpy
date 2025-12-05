import rich_click as click
from rich.console import Console
from rich.tree import Tree

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.core.backup import BackupSpace

palette = get_default_palette()


@click.command("list", help="List information about the available backup spaces.")
@click.option(
    "--depth",
    type=int,
    default=1,
    help="The amount of details to show for each remote. Default is 1.",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Activate the debug log for the command "
    "to print full error traces in case of a problem.",
)
def list_spaces(depth: int, debug: bool) -> None:
    tree = Tree(f"{palette.mauve}Backup Spaces{RESET}")

    try:
        spaces = BackupSpace.get_backup_spaces()
    except Exception as e:
        return print_error_message(error=e, debug=debug)

    for space in spaces:
        space_branch = tree.add(
            f"{palette.sky}{space.get_name()} {palette.lavender}"
            f"(UUID: {space.get_uuid()}){RESET}",
        )
        if depth > 1:
            space_branch.add(
                f"{palette.lavender}Type: {palette.maroon}{space.get_type().name}{RESET}"
            )
        if depth > 2:
            remote_str = f"{space.get_remote().get_name()} (UUID: {space.get_remote().get_uuid()})"
            space_branch.add(
                f"{palette.lavender}Remote: {palette.maroon}{remote_str}{RESET}"
            )
        if depth > 3:
            space_branch.add(
                f"{palette.lavender}Compression Algorithm: {palette.maroon}"
                f"{space.get_compression_algorithm().name}{RESET}"
            )
            space_branch.add(
                f"{palette.lavender}Compression Level: {palette.maroon}"
                f"{space.get_compression_level()}{RESET}"
            )
        if depth > 4:
            space_branch.add(
                f"{palette.lavender}Include: {palette.maroon}{space.get_default_include()}{RESET}"
            )
            space_branch.add(
                f"{palette.lavender}Exclude: {palette.maroon}{space.get_default_exclude()}{RESET}"
            )

    Console().print(tree)

    return None
