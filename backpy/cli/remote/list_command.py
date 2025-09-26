import click
from rich.console import Console
from rich.tree import Tree

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.core.remote import Remote

palette = get_default_palette()


@click.command(
    "list",
    help="List information about the available remotes.",
)
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
def list_remotes(depth: int, debug: bool) -> None:

    tree = Tree(f"{palette.mauve}Remotes{RESET}")

    try:
        remotes = Remote.get_remotes()
    except Exception as e:
        return print_error_message(error=e, debug=debug)

    for remote in remotes:
        remote_branch = tree.add(
            f"{palette.sky}{remote.get_name()} {palette.lavender}"
            f"(UUID: {remote.get_uuid()}){RESET}",
        )
        if depth > 1:
            remote_branch.add(
                f"{palette.lavender}Protocol: {palette.maroon}{remote.get_protocol().name}{RESET}"
            )
        if depth > 2:
            remote_branch.add(
                f"{palette.lavender}Hostname: {palette.maroon}{remote.get_hostname()}{RESET}"
            )
            remote_branch.add(
                f"{palette.lavender}Username: {palette.maroon}{remote.get_username()}{RESET}"
            )
        if depth > 3:
            remote_branch.add(
                f"{palette.lavender}Authentication: {palette.maroon}"
                f"{'SSH-Key' if remote.get_ssh_key() is not None else 'Password'}{RESET}"
            )
            if remote.get_ssh_key() is not None:
                remote_branch.add(
                    f"{palette.lavender}Keyfile: {palette.maroon}{remote.get_ssh_key()}{RESET}"
                )

    Console().print(tree)

    return None
