import click
from rich.console import Console
from rich.tree import Tree

from backpy.cli.colors import RESET, get_default_palette

palette = get_default_palette()


@click.command(
    "list",
    help=f"List all backups in a {palette.sky}'BACKUP_SPACE'{RESET} "
    f"identified by its UUID or name.",
)
@click.argument("schedule", type=str, default=None, required=True)
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
def list_schedules(
    backup_space: str | None,
    sort_by: str,
    check_hash: bool,
    verbose: int,
    depth: int,
    debug: bool,
) -> None:

    verbose += 1

    tree = Tree(
        f"{palette.mauve}Schedules"
        f"\n{palette.mauve}Sorted by: {palette.lavender}{sort_by}{RESET}"
    )

    Console().print(tree)

    return None
