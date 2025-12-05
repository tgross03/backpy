import rich_click as click

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.core.remote import Remote
from backpy.core.utils.exceptions import InvalidRemoteError

palette = get_default_palette()


@click.command(
    "test",
    help=f"Test the connection of a {palette.sky}'REMOTE'{RESET} identified by "
    f"its name or UUID.",
)
@click.argument("remote", type=str, required=True)
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
def test(remote: str, verbose: int, debug: bool) -> None:

    verbose += 1

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

    try:
        remote.test_connection(verbosity_level=verbose)
    except Exception as e:
        return print_error_message(
            error=e,
            debug=debug,
        )

    return None
