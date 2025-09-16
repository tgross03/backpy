from pathlib import Path

import click

from backpy import Protocol, Remote, VariableLibrary
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import (
    ConfirmInput,
    FilePathInput,
    IntegerInput,
    PasswordInput,
    TextInput,
    print_error_message,
)
from backpy.core.remote.remote import _protocols
from backpy.core.utils.exceptions import InvalidRemoteError

palette = get_default_palette()

protocol_names = [protocol.name for protocol in _protocols]


def create_interactive(verbosity_level: int, debug: bool) -> None:

    unique_name = False

    while not unique_name:
        name = TextInput(
            message=f"{palette.base}> Enter an alias for the remote:{RESET}",
            invalid_error_message=f"{palette.maroon}The alias may not be empty!{RESET}",
        ).prompt()

        try:
            Remote.load_by_name(name=name)
        except InvalidRemoteError:
            break

        print(
            f"{palette.red}ERROR:{palette.maroon} The given name is already "
            f"taken by another remote. The provided name has to be unique!"
        )
        continue

    protocol = TextInput(
        message=f"{palette.base}> Enter the desired transfer protocol "
        f"({palette.overlay1}available: {', '.join(protocol_names)}{palette.base}):{RESET}",
        suggest_matches=True,
        suggestible_values=protocol_names,
        invalid_error_message=f"{palette.maroon}Invalid protocol! Please try again.{RESET}",
    ).prompt()

    protocol = Protocol.from_name(name=protocol)

    hostname = TextInput(
        message=f"{palette.base}> Enter the hostname of the remote:{RESET}",
        invalid_error_message=f"{palette.maroon}The alias may not be empty!{RESET}",
    ).prompt()

    username = TextInput(
        message=f"{palette.base}> Enter the username with which to connect to the remote:{RESET}",
        invalid_error_message=f"{palette.maroon}The username may not be empty!{RESET}",
    ).prompt()

    key_path = None
    password = None
    use_system_keys = False

    if protocol.supports_ssh_keys:
        key_path = FilePathInput(
            message=f"{palette.base}> Enter the path to an SSH key which should be used to connect "
            f"to the remote (optional):{RESET}",
            allow_none=True,
        ).prompt()

        if key_path is not None:
            password = PasswordInput(
                message=f"{palette.base}> Enter the passphrase of the SSH key "
                f"(may be empty):{RESET}",
                allow_empty=True,
                confirm_input=False,
            ).prompt()

        use_system_keys = ConfirmInput(
            message=f"{palette.base}> Should backpy try to use SSH keys from your system's "
            f"SSH agent for authentication?{RESET}",
            default_value=False,
        ).prompt()

    if not protocol.supports_ssh_keys or key_path is None:
        password = PasswordInput(
            message=f"{palette.base}> Enter the password for the user:{RESET}",
            allow_empty=False,
            confirm_input=False,
        ).prompt()

    timeout = IntegerInput(
        message=f"{palette.base}> Enter the maximum duration in seconds "
        f"to wait for the connection:{RESET}",
        default_value=None,
        allow_none=True,
    ).prompt()

    root_dir = TextInput(
        message=f"{palette.base}> Enter the root directory of backpy on the remote:{RESET}",
        default_value=VariableLibrary().get_variable(
            "backup.states.default_remote_root_dir"
        ),
    ).prompt()

    sha256_cmd = TextInput(
        message=f"{palette.base}> Enter the shell command to calculate a file's SHA-256 sum on "
        f"the remote server:{RESET}",
        default_value=VariableLibrary().get_variable(
            "backup.states.default_sha256_cmd"
        ),
    ).prompt()

    remote = Remote.new(
        name=name,
        protocol=protocol.name,
        hostname=hostname,
        username=username,
        password=password,
        ssh_key=key_path,
        use_system_keys=use_system_keys,
        connection_timeout=timeout,
        root_dir=root_dir,
        sha256_cmd=sha256_cmd,
        verbosity_level=verbosity_level,
        test_connection=False,
    )

    try:
        remote.test_connection(verbosity_level=verbosity_level)
    except Exception as e:
        print_error_message(error=e, debug=debug)
        print(
            f"{palette.red}HINT:{palette.maroon} If you are experiencing connection problems "
            f"due to wrong settings of the remote, edit or remove it via the CLI."
        )

    return None


@click.command("create", help="Create a remote to save backups at.")
@click.option("--name", "-n", type=str, default="", help="The alias of the remote.")
@click.option(
    "--protocol",
    "-p",
    type=click.types.Choice(protocol_names),
    default="scp",
    help="The transfer protocol to use for the file up- and download.",
)
@click.option(
    "--hostname",
    "-h",
    type=str,
    default="",
    help="The hostname / IP of the remote server.",
)
@click.option(
    "--username",
    "-u",
    type=str,
    default="",
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
    "--use-system-keys",
    type=click.BOOL,
    default=False,
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
    default=VariableLibrary().get_variable("backup.states.default_remote_root_dir"),
    help="The backpy root directory on the remote server. If not set, the default value set in the "
    "variable configuration is used.",
)
@click.option(
    "--sha256-cmd",
    type=str,
    default=VariableLibrary().get_variable("backup.states.default_sha256_cmd"),
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
    help="Activate the debug log for the command or interactive "
    "mode to print full error traces in case of a problem.",
)
@click.option(
    "--interactive", "-i", is_flag=True, help="Create the remote in interactive mode."
)
def create(
    name: str,
    protocol: str,
    hostname: str,
    username: str,
    key: Path | None,
    use_system_keys: bool,
    timeout: int | None,
    root_dir: str,
    sha256_cmd: str,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:

    verbose += 1

    if interactive:
        return create_interactive(verbosity_level=verbose, debug=debug)

    try:
        Remote.load_by_name(name=name)
    except InvalidRemoteError:
        pass
    else:
        return print_error_message(
            error=NameError(
                "The given name is already "
                "taken by another remote. The provided name has to be unique!"
            ),
            debug=debug,
        )

    if hostname == "":
        return print_error_message(
            error=ValueError("The hostname may not be empty!"), debug=debug
        )

    if username == "":
        return print_error_message(
            error=ValueError("The username may not be empty!"), debug=debug
        )

    if key is not None:
        password = PasswordInput(
            message=f"{palette.base}> Enter the passphrase for the SSH key (may be empty):{RESET}",
            allow_empty=True,
            confirm_input=False,
        ).prompt()
    else:
        password = PasswordInput(
            message=f"{palette.base}> Enter the password for the user:{RESET}",
            allow_empty=False,
            confirm_input=False,
        ).prompt()

    remote = Remote.new(
        name=name,
        protocol=protocol,
        hostname=hostname,
        username=username,
        password=password,
        ssh_key=key,
        use_system_keys=use_system_keys,
        connection_timeout=timeout,
        root_dir=root_dir,
        sha256_cmd=sha256_cmd,
        verbosity_level=verbose,
        test_connection=False,
    )
    try:
        remote.test_connection(verbosity_level=verbose)
    except Exception as e:
        print_error_message(error=e, debug=debug)
        print(
            f"{palette.red}HINT:{palette.maroon} If you are experiencing connection problems "
            "due to wrong settings of the remote, edit or remove it via the CLI."
        )

    return None
