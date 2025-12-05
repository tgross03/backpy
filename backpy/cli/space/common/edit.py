from typing import Callable

import click

from backpy import BackupSpace, BackupSpaceType, Remote
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import ConfirmInput, print_error_message
from backpy.core.backup import compression
from backpy.core.backup.compression import CompressionAlgorithm
from backpy.core.utils.exceptions import InvalidBackupSpaceError, InvalidRemoteError

palette = get_default_palette()


def edit_backup_space(
    backup_space: str,
    compression_algorithm: str | None,
    compression_level: int | None,
    default_include: list[str] | None,
    default_exclude: list[str] | None,
    remote: str | None,
    force: bool,
    verbose: int,
    debug: bool,
    additional_values: dict,
) -> None:
    verbose += 1

    try:
        space = BackupSpace.load_by_uuid(backup_space)
    except Exception:
        try:
            space = BackupSpace.load_by_name(backup_space)
        except Exception:
            return print_error_message(
                InvalidBackupSpaceError(
                    "There is no Backup Space with that name or UUID!"
                ),
                debug=debug,
            )

    space = space.get_as_child_class()

    prev_config = space.get_config().copy()

    for key, value in additional_values.items():
        space.__dict__[key] = value

    if compression_algorithm is not None:
        space._compression_algorithm = CompressionAlgorithm.from_name(
            name=compression_algorithm
        )

    if compression_level is not None:
        space._compression_level = compression_level

    if default_include is not None:
        if isinstance(default_include, str):
            default_include = [default_include]
        space._default_include = default_include

    if default_exclude is not None:
        if isinstance(default_exclude, str):
            default_exclude = [default_exclude]
        space._default_exclude = default_exclude

    if remote is not None:

        if remote == "None":
            remote = None
        else:

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
            remote_str = (
                f"{palette.sky}{remote.get_name()} (UUID: {remote.get_uuid()}){RESET}"
                if remote is not None
                else "None"
            )
            confirm = ConfirmInput(
                message=f"> Are you sure you want to change the remote of this backup "
                f"space to {remote_str}?\n{palette.red}WARNING! "
                f"{palette.maroon}This might affect every backup which is saved on this "
                f"remote! Some backups might become unrestorable!{RESET}",
                default_value=False,
            ).prompt()

        if confirm:
            space._remote = remote

            if remote is not None:
                with space.get_remote()(context_verbosity=verbose) as remote:
                    remote.mkdir(
                        target=space.get_remote_path(),
                        parents=True,
                        verbosity_level=verbose,
                    )

        else:
            print(
                f"{palette.maroon}Remote change canceled. "
                f"All other changes will be applied{RESET}"
            )

    space.update_config()

    if space.get_config() == prev_config and verbose >= 1:
        print(f"{palette.flamingo}Nothing to update. No changes applied.{RESET}")
    elif verbose >= 1:
        print(
            f"{palette.base}Update applied to backup space {palette.sky}{space.get_uuid()}"
            f"{palette.base}.{RESET}"
        )

    return None


def common_options(space_type: BackupSpaceType) -> Callable:
    def decorator(func: Callable) -> Callable:
        func = click.argument(
            "backup_space",
            type=str,
            required=True,
        )(func)
        func = click.option(
            "--compression-algorithm",
            type=click.Choice(
                [method.name for method in compression._compression_methods]
            ),
            default=None,
            help="The compression algorithm to be used to compress the backed up files.",
        )(func)
        func = click.option(
            "--compression-level",
            type=click.IntRange(0, 9),
            default=None,
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
            "should be send. If set to 'None', the existing remote will be removed.",
        )(func)
        func = click.option(
            "--force",
            "-f",
            is_flag=True,
            help="Force changes that might lead to data loss. "
            "This will skip the confirmation step.",
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
        return func

    return decorator
