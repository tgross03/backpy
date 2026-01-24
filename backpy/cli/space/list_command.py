import rich_click as click
from rich.console import Console
from rich.tree import Tree

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.core.space import BackupSpace
from backpy.core.utils import bytes2str

palette = get_default_palette()


@click.command("list", help="List information about the available backup spaces.")
@click.option(
    "--depth",
    type=int,
    default=1,
    help="The amount of details to show for each backup space. Default is 1.",
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
    help="Activate the debug log for the command "
    "to print full error traces in case of a problem.",
)
def list_spaces(depth: int, verbose: int, debug: bool) -> None:
    verbose += 1

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
            if space.get_remote() is not None:
                remote_str = (
                    f"{space.get_remote().get_name()} "
                    f"(UUID: {space.get_remote().get_uuid()})"
                )
                space_branch.add(
                    f"{palette.lavender}Remote: {palette.maroon}{remote_str}{RESET}"
                )
        if depth > 3:
            disk_usage_str = (
                f"{bytes2str(space.get_disk_usage(verbosity_level=verbose))} / "
                f"{bytes2str(space.get_max_size())}"
            )
            space_branch.add(
                f"{palette.lavender}Disk Usage: {palette.maroon}{disk_usage_str}{RESET}"
            )
            num_backups_str = (
                f"{len(space.get_backups())} / "
                f"{'∞' if space.get_max_backups() == -1 else space.get_max_backups()}"
            )
            space_branch.add(
                f"{palette.lavender}Number of Backups: {palette.maroon}{num_backups_str}{RESET}"
            )
            auto_deletion_active = space.is_auto_deletion_active()
            space_branch.add(
                f"{palette.lavender}Auto Deletion Active: {palette.maroon}"
                f"{auto_deletion_active}{RESET}"
            )
            if auto_deletion_active:
                auto_deletion_rule = space.get_auto_deletion_rule()
                space_branch.add(
                    f"{palette.lavender}Auto Deletion Rule: {palette.maroon}"
                    f"{auto_deletion_rule}{RESET}"
                )

        if depth > 4:
            space_branch.add(
                f"{palette.lavender}Compression Algorithm: {palette.maroon}"
                f"{space.get_compression_algorithm().name}{RESET}"
            )
            space_branch.add(
                f"{palette.lavender}Compression Level: {palette.maroon}"
                f"{space.get_compression_level()}{RESET}"
            )
        if depth > 5:
            space_branch.add(
                f"{palette.lavender}Include: {palette.maroon}{space.get_default_include()}{RESET}"
            )
            space_branch.add(
                f"{palette.lavender}Exclude: {palette.maroon}{space.get_default_exclude()}{RESET}"
            )

    Console().print(tree)

    return None
