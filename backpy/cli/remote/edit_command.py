from pathlib import Path

import click

from backpy import Protocol, Remote
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import PasswordInput, print_error_message
from backpy.core.remote.password import encrypt
from backpy.core.remote.remote import _protocols
from backpy.core.utils.exceptions import InvalidRemoteError

protocol_names = [protocol.name for protocol in _protocols]

palette = get_default_palette()


@click.command(
    "edit",
    help=f"Edit a {palette.sky}'REMOTE'{RESET} identified by its name or UUID.",
)
@click.argument("remote", type=str, required=True)
@click.option("--name", "-n", type=str, default=None, help="The alias of the remote.")
@click.option(
    "--protocol",
    "-p",
    type=click.types.Choice(protocol_names),
    default=None,
    help="The transfer protocol to use for the file up- and download.",
)
@click.option(
    "--hostname",
    "-h",
    type=str,
    default=None,
    help="The hostname / IP of the remote server.",
)
@click.option(
    "--username",
    "-u",
    type=str,
    default=None,
    help="The name of the user to connect with.",
)
@click.option(
    "--key",
    "-k",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="The path to a SSH-Key to use for connecting to the remote. This requires the chosen "
    "protocol to support SSH key authentification. The given file may be protected with a "
    "passphrase which has to be entered interactively. The usage of SSH keys is optional but "
    "recommended if possible.",
)
@click.option(
    "--password",
    is_flag=True,
    help="Whether to change the password / passphrase. Do not enter a password here! "
    "This will trigger a dialog to change the password in!",
)
@click.option(
    "--use-system-keys",
    type=click.BOOL,
    default=None,
    help="Whether to attempt the usage of keys saved in the system's agent.",
)
@click.option(
    "--timeout",
    type=int,
    default=None,
    help="The time in seconds to wait for the connection to complete.",
)
@click.option(
    "--root-dir",
    type=str,
    default=None,
    help="The backpy root directory on the remote server. If not set, the default value set in the "
    "variable configuration is used.",
)
@click.option(
    "--sha256-cmd",
    type=str,
    default=None,
    help="The shell command to calculate a file's SHA-256 sum on the remote server. "
    "If not set, the default value set in the variable configuration is used.",
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
def edit(
    remote: str,
    name: str | None,
    protocol: str | None,
    hostname: str | None,
    username: str | None,
    key: Path | None,
    password: bool,
    use_system_keys: bool | None,
    timeout: int | None,
    root_dir: str | None,
    sha256_cmd: str | None,
    verbose: int,
    debug: bool,
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

    remote.disconnect(verbosity_level=verbose)

    if name is not None:
        remote._name = name

    if protocol is not None:
        remote._protocol = Protocol.from_name(protocol)

    if hostname is not None:
        remote._hostname = hostname

    if username is not None:
        remote._username = username

    if key is not None:
        remote._ssh_key = key

    if use_system_keys is not None:
        remote._use_system_keys = use_system_keys

    if password:
        if remote.get_ssh_key() is not None:
            password = PasswordInput(
                message=f"{palette.base}> Enter the new passphrase of the SSH key "
                f"(may be empty):{RESET}",
                allow_empty=True,
                confirm_input=True,
            ).prompt()
        else:
            password = PasswordInput(
                message=f"{palette.base}> Enter the new password for the user:{RESET}",
                allow_empty=False,
                confirm_input=True,
            ).prompt()

        remote._token = encrypt(password)

    if timeout is not None:
        remote._connection_timeout = timeout

    if root_dir is not None:
        remote._root_dir = root_dir

    if sha256_cmd is not None:
        remote._sha256_cmd = sha256_cmd

    if verbose > 1:
        print(f"Updating the configuration file at {remote._config.get_path()}")

    remote.update_config()

    return None
