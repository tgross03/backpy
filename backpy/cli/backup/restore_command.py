import rich_click as click
from rich.console import Console

from backpy.cli.colors import EFFECTS, RESET, get_default_palette
from backpy.cli.elements import (
    BackupInput,
    BackupSpaceInput,
    ConfirmInput,
    TextInput,
    print_error_message,
)
from backpy.core.backup import Backup, RestoreMode
from backpy.core.space import BackupSpace
from backpy.core.utils.exceptions import (
    InvalidBackupError,
    InvalidBackupSpaceError,
    InvalidChecksumError,
)

palette = get_default_palette()


def restore_interactive(force: bool, debug: bool, verbosity_level: int):
    space = BackupSpaceInput(suggest_matches=True).prompt()

    if len(space.get_backups(check_hash=False)) == 0:
        return print_error_message(
            InvalidBackupError("There is no Backup present in this Backup Space!"),
            debug=debug,
        )

    backup = BackupInput(backup_space=space, suggest_matches=True).prompt()

    if backup.has_remote_archive() and backup.has_local_archive():
        source = TextInput(
            message=f"{palette.base}> From where do you want to restore to the backup file? "
            f"('local' or 'remote') {RESET}",
            suggest_matches=True,
            suggestible_values=["local", "remote"],
            default_value="local" if backup.has_local_archive() else "remote",
        ).prompt()
    elif backup.has_remote_archive() and not backup.has_local_archive():
        source = "remote"
    else:
        source = "local"

    modes = space.get_type().supported_restore_modes
    mode_list = "\n".join(
        [
            f" - {palette.base}{EFFECTS.bold.on}{m.name}{RESET}{palette.maroon} -> "
            f"{EFFECTS.dim.on}{m.description}{RESET}"
            for m in modes
        ]
    )

    mode = TextInput(
        message=f"{palette.base}> Which mode should be used to restore the backup?"
        "\nAvailable modes:\n"
        f"{mode_list}\n",
        suggest_matches=True,
        suggestible_values=[m.name for m in modes],
    ).prompt()

    mode = RestoreMode[mode]

    Console().print(backup.get_info_table())
    print(
        f"{palette.base}Restore mode: {palette.maroon}{mode.name} "
        f"({EFFECTS.dim.on}{mode.description}{EFFECTS.dim.off}){RESET}"
    )

    if not force:

        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to restore backup "
            f"{palette.maroon}{str(backup.get_uuid())}{palette.base}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            try:
                backup.restore(
                    mode=mode,
                    source=source,
                    force=force,
                    verbosity_level=verbosity_level,
                )
            except InvalidChecksumError as e:
                print_error_message(
                    error=e,
                    debug=debug,
                )
        else:
            print(
                f"{palette.red}Canceled restoring of backup "
                f"{palette.maroon}{str(backup.get_uuid())}{palette.red}.{RESET}"
            )
    else:
        backup.restore(mode=mode, source=source, verbosity_level=verbosity_level)

    return None


all_mode_list = ", ".join(
    [
        f"{EFFECTS.bold.on}{mode.name}{RESET} -> "
        f"{EFFECTS.dim.on}{mode.description}{RESET}"
        for mode in list(RestoreMode.__members__.values())
    ]
)


@click.command(
    "restore",
    help=f"Restore a {palette.sky}'BACKUP'{RESET} identified by its UUID or a "
    f"keyword ('latest', 'oldest' or 'largest', 'smallest') "
    f"to a {palette.sky}'BACKUP_SPACE'{RESET} identified by its UUID or name.",
)
@click.argument("backup_space", type=str, default=None, required=False)
@click.argument("backup", type=str, default=None, required=False)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(list(RestoreMode.__members__.keys())),
    default=None,
    help=f"The mode to restore the backup with. Available modes are:\n"
    f"{all_mode_list}",
)
@click.option(
    "--source",
    "-s",
    type=click.Choice(["local", "remote"]),
    default="local",
    help="The location from which to restore the backup.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the deletion of the backup. This will skip the confirmation step.",
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
    "--interactive", "-i", is_flag=True, help="Delete the backup in interactive mode."
)
def restore(
    backup_space: str | None,
    backup: str | None,
    mode: str | None,
    source: str,
    force: bool,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:
    verbose += 1

    if interactive:
        return restore_interactive(force=force, debug=debug, verbosity_level=verbose)

    if backup_space is None or backup is None:
        return print_error_message(
            ValueError(
                "If the '--interactive' flag is not given, you have to supply "
                "a valid value for the 'BACKUP_SPACE' and 'BACKUP' arguments."
            ),
            debug=debug,
        )

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

    modes = space.get_type().supported_restore_modes

    mode_list = "\n".join(
        [
            f" - {EFFECTS.bold.on}{m.name}{RESET}{palette.maroon} -> {m.description}"
            for m in modes
        ]
    )

    if mode is None:
        return print_error_message(
            error=ValueError(
                "If the '--interactive' flag is not given, you have to supply "
                "a valid value for '--mode' option has to be provided!\nAvailable modes:\n"
                f"{mode_list}"
            ),
            debug=debug,
        )

    if mode not in modes:
        return print_error_message(
            error=ValueError(
                f"The given mode '{mode}' is not available for a backup "
                f"space of type '{space.get_type().name}'!\nAvailable modes:\n"
                f"{mode_list}"
            ),
            debug=debug,
        )

    space = space.get_as_child_class()

    if len(space.get_backups(check_hash=False)) == 0:
        return print_error_message(
            InvalidBackupError("There is no Backup present in this Backup Space!"),
            debug=debug,
        )

    match backup:
        case "oldest":
            backup = space.get_backups(sort_by="date", check_hash=False)[-1]
        case "newest":
            backup = space.get_backups(sort_by="date", check_hash=False)[0]
        case "largest":
            backup = space.get_backups(sort_by="size", check_hash=False)[0]
        case "smallest":
            backup = space.get_backups(sort_by="size", check_hash=False)[-1]
        case _:
            try:
                backup = Backup.load_by_uuid(
                    backup_space=space, unique_id=backup, verbosity_level=verbose
                )
            except Exception:
                return print_error_message(
                    InvalidBackupError(
                        f"There is no Backup with that UUID in the Backup "
                        f"Space '{space.get_name()}'"
                    ),
                    debug=debug,
                )

    mode = RestoreMode[mode]

    if source == "remote" and not backup.has_remote_archive():
        return print_error_message(
            InvalidBackupError(
                f"The backup '{backup.get_uuid()}' does not have a remote backup file."
            ),
            debug=debug,
        )
    elif source == "local" and not backup.has_local_archive():
        return print_error_message(
            InvalidBackupError(
                f"The backup '{backup.get_uuid()}' does not have a local backup file."
            ),
            debug=debug,
        )

    Console().print(backup.get_info_table())
    print(
        f"{palette.base}Restore mode: {palette.maroon}{mode.name} "
        f"({EFFECTS.dim.on}{mode.description}{EFFECTS.dim.off}){RESET}"
    )

    if not force:
        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to restore backup "
            f"{palette.maroon}{str(backup.get_uuid())}{palette.base}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            try:
                backup.restore(
                    mode=mode,
                    source=source,
                    force=force,
                    verbosity_level=verbose,
                )
            except InvalidChecksumError as e:
                print_error_message(
                    error=e,
                    debug=debug,
                )
        else:
            print(
                f"{palette.red}Canceled restoring of backup "
                f"{palette.maroon}{str(backup.get_uuid())}{palette.red}.{RESET}"
            )
    else:
        backup.restore(mode=mode, source=source, force=force, verbosity_level=verbose)

    return None
