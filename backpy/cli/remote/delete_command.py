import rich_click as click

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import ConfirmInput, print_error_message
from backpy.core.remote import Remote
from backpy.core.utils.exceptions import InvalidRemoteError

palette = get_default_palette()


@click.command(
    "delete",
    help=f"Delete a {palette.sky}'REMOTE'{RESET} identified by its name or UUID.",
)
@click.argument("remote", type=str, required=True)
@click.option(
    "--delete-files", is_flag=True, help="Delete all backup spaces on the remote."
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the deletion. This will skip the confirmation step.",
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
def delete(
    remote: str, delete_files: bool, force: bool, verbose: int, debug: bool
) -> None:
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

    confirm = False or force

    if not force:
        confirm = ConfirmInput(
            message=f"> Are you sure you want to delete the remote "
            f"{palette.sky}{remote.get_name()} "
            f"(UUID: {remote.get_uuid()}){RESET}?\n{palette.red}WARNING! "
            f"{palette.maroon}This cannot be undone and will affect every backup "
            f"which uses this remote! Some backups might become unrestorable!{RESET}",
            default_value=False,
        ).prompt()

    if confirm:
        remote.delete(delete_files=delete_files, verbosity_level=verbose)
    else:
        print(f"{palette.maroon}Deletion canceled.{RESET}")

    return None
