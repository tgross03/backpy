import click
from rich import box
from rich.console import Console
from rich.table import Table

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.core.remote import Remote
from backpy.core.utils.exceptions import InvalidRemoteError

palette = get_default_palette()


@click.command(
    "info",
    help=f"Show information about a specific {palette.sky}'REMOTE'{RESET} identified by "
    f"its name or UUID.",
)
@click.argument("remote", type=str, required=True)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Activate the debug log for the command "
    "to print full error traces in case of a problem.",
)
def info(remote: str, debug: bool) -> None:

    try:
        remote = Remote.load_by_uuid(unique_id=remote)
    except Exception:
        try:
            remote = Remote.load_by_name(name=remote)
        except Exception:
            return print_error_message(
                error=InvalidRemoteError(
                    "The given name or UUID does not match any remote's name or UUID!"
                ),
                debug=debug,
            )

    table = Table(
        title=f"{palette.peach}REMOTE INFORMATION{RESET}",
        show_header=False,
        show_edge=True,
        header_style=palette.overlay1,
        box=box.HORIZONTALS,
        expand=False,
        pad_edge=False,
    )

    table.add_column(justify="right", no_wrap=False)
    table.add_column(justify="left", no_wrap=False)

    table.add_row(f"{palette.sky}Name", f"{palette.base}{remote.get_name()}")
    table.add_row(f"{palette.sky}UUID", f"{palette.base}{remote.get_uuid()}")
    table.add_row(
        f"{palette.sky}Protocol", f"{palette.base}{remote.get_protocol().name}"
    )
    table.add_row(f"{palette.sky}Hostname", f"{palette.base}{remote.get_hostname()}")
    table.add_row(f"{palette.sky}Username", f"{palette.base}{remote.get_username()}")
    table.add_row(
        f"{palette.sky}Authentication",
        f"{palette.base}{'SSH-Key' if remote.get_ssh_key() is not None else 'Password'}",
    )
    if remote.get_ssh_key() is not None:
        table.add_row(f"{palette.sky}Keyfile", f"{palette.base}{remote.get_ssh_key()}")
    table.add_row(
        f"{palette.sky}Use System Keys?",
        f"{palette.base}{'yes' if remote.should_use_system_keys() else 'no'}",
    )

    timeout = remote.get_connection_timeout()
    table.add_row(
        f"{palette.sky}Connection Timeout",
        f"{palette.base}{timeout if timeout is not None else 'none'}",
    )
    table.add_row(
        f"{palette.sky}Root Directory", f"{palette.base}{remote.get_root_dir()}"
    )
    table.add_row(
        f"{palette.sky}SHA-256 Command", f"{palette.base}{remote.get_sha256_cmd()}"
    )

    Console().print(table)

    return None
