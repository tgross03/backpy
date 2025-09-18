from typing import Callable

import click

from backpy import BackupSpace, BackupSpaceType, Remote, VariableLibrary
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import (
    EnumerationInput,
    IntegerInput,
    RemoteInput,
    TextInput,
    print_error_message,
)
from backpy.core.backup import compression
from backpy.core.utils.exceptions import InvalidRemoteError

palette = get_default_palette()

# TODO: CHECK PATH OF CREATED SPACES (expand ~ and absolute path were wrong)


def create_backup_space_interactive(
    func: Callable, space_type: BackupSpaceType, verbosity_level: int, debug: bool
):

    unique_name = False
    while not unique_name:
        name = TextInput(
            message=f"> Enter the name for the {space_type.full_name}:",
        ).prompt()

        try:
            BackupSpace.load_by_name(name=name)
        except Exception:
            break

        print(
            f"{palette.red}ERROR:{palette.maroon} The given name is already "
            f"taken by another backup space. The provided name has to be unique!"
        )

    kwargs = func()

    compression_algorithm = TextInput(
        message="> Enter the compression algorithm to be used to compress the backed up files:",
        suggest_matches=True,
        default_value=VariableLibrary().get_variable(
            "backup.states.default_compression_algorithm"
        ),
        suggestible_values=[method.name for method in compression._compression_methods],
    ).prompt()

    algorithm = compression.CompressionAlgorithm.from_name(name=compression_algorithm)

    if algorithm.allows_compression_level:
        compression_level = IntegerInput(
            message="> Enter the compression level to which the backed up files should "
            "be compressed:",
            default_value=VariableLibrary().get_variable(
                "backup.states.default_compression_level"
            ),
            min_value=0,
            max_value=9,
        ).prompt()
    else:
        compression_level = (
            VariableLibrary().get_variable("backup.states.default_compression_level"),
        )

    if space_type.use_inclusion:
        default_include = EnumerationInput(
            message=f"{palette.base}> Enter a comma-seperated enumeration of {palette.lavender}"
            f"elements that should be {palette.maroon}included{palette.lavender} in the "
            f"backup{palette.base} "
            f"(e.g. paths, patterns, tables, databases) (if empty every non-excluded element "
            f"will be used):{RESET}",
            default_value="",
        ).prompt()
    else:
        default_include = []

    if space_type.use_exclusion:
        default_exclude = EnumerationInput(
            message=f"{palette.base}> Enter n comma-seperated enumeration of {palette.lavender}"
            f"elements that should be excluded from the backups by default{palette.base} "
            f"(e.g. paths, patterns, tables, databases) (can be empty):{RESET}",
            default_value="",
        ).prompt()
    else:
        default_exclude = []

    remote = RemoteInput(allow_none=True, suggest_matches=True).prompt()

    space_type.child_class.new(
        name=name,
        compression_algorithm=compression_algorithm,
        compression_level=compression_level,
        default_include=default_include,
        default_exclude=default_exclude,
        remote=remote,
        verbosity_level=verbosity_level,
        **kwargs,
    )

    return None


def create_backup_space(
    name: str,
    space_type: str,
    compression_algorithm: str,
    compression_level: int,
    default_include: list[str],
    default_exclude: list[str],
    remote: str,
    verbose: int,
    debug: bool,
    interactive: bool,
    interactive_func: Callable,
    **kwargs,
) -> None:
    verbose += 1

    backup_space_type = BackupSpaceType.from_name(name=space_type)

    if interactive:
        return create_backup_space_interactive(
            func=interactive_func,
            space_type=backup_space_type,
            verbosity_level=verbose,
            debug=debug,
        )

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

    backup_space_type.child_class.new(
        name=name,
        compression_algorithm=compression_algorithm,
        compression_level=compression_level,
        default_include=default_include,
        default_exclude=default_exclude,
        remote=remote,
        verbosity_level=verbose,
        **kwargs,
    )

    return None


def common_options(space_type: BackupSpaceType) -> Callable:
    def decorator(func: Callable) -> Callable:
        func = click.argument(
            "name",
            type=str,
            default="",
        )(func)
        func = click.option(
            "--compression_algorithm",
            type=click.Choice(
                [method.name for method in compression._compression_methods]
            ),
            default=VariableLibrary().get_variable(
                "backup.states.default_compression_algorithm"
            ),
            help="The compression algorithm to be used to compress the backed up files.",
        )(func)
        func = click.option(
            "--compression_level",
            type=click.IntRange(0, 9),
            default=VariableLibrary().get_variable(
                "backup.states.default_compression_level"
            ),
            help="The compression level to which the backed up files should be compressed. "
            "Depending on the compression algorithm this might not have an effect.",
        )(func)
        if space_type.use_inclusion:
            func = click.option(
                "--default-include",
                type=str,
                multiple=True,
                default=None,
                help="A list of elements (e.g. paths, patterns, tables, databases) to include. "
                "If not set, every non-excluded element will be used backed up. "
                "Depending on the Backup Space this might not have an effect. "
                "Important: Symbols like ',' and '\"' have to be escaped!",
            )(func)
        if space_type.use_exclusion:
            func = click.option(
                "--default-exclude",
                multiple=True,
                default=None,
                help="A list of elements (e.g. paths, patterns, tables, databases) to exclude "
                "in every backup. Depending on the Backup Space this might not have an effect. "
                "Important: Symbols like ',' and '\"' have to be escaped!",
            )(func)
        func = click.option(
            "--remote",
            "-r",
            type=str,
            default=None,
            help="The name or UUID of the remote to which the backups for this backup space "
            "should be send.",
        )(func)
        func = click.option(
            "--verbose",
            "-v",
            count=True,
            help="Sets the verbosity level of the output.",
        )(func)
        func = click.option(
            "--debug",
            "-d",
            is_flag=True,
            help="Activate the debug log for the command or interactive "
            "mode to print full error traces in case of a problem.",
        )(func)
        func = click.option(
            "--interactive",
            "-i",
            is_flag=True,
            help="Create the backup in interactive mode.",
        )(func)
        return func

    return decorator
