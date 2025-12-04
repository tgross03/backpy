import click
from rich.console import Console

from backpy import Backup, BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import (
    BackupInput,
    BackupSpaceInput,
    ConfirmInput,
    TextInput,
    print_error_message,
)
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

    if backup.get_remote() is not None:
        source = TextInput(
            message=f"{palette.base}From where do you want to restore to the backup file? "
            f"('local' or 'remote') {RESET}",
            suggest_matches=True,
            suggestible_values=["local", "remote"],
            default_value="local",
        ).prompt()
    else:
        source = "local"

    incremental = ConfirmInput(
        message=f"{palette.base}Do you want to restore the backup incrementally? "
        "This means that only content, which is included in the backup "
        "will be affected. If this is 'False', the contents will be deleted and replaced "
        f"by the backed up content.{RESET}",
        default_value=True,
    ).prompt()

    Console().print(backup.get_info_table())
    print(
        f"{palette.base}Restore mode: {palette.maroon}{'incremental' if incremental else 'non-incremental'}{RESET}"
    )

    if not force:

        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to restore backup "
            f"{palette.maroon}{str(backup.get_uuid())} (Created at: "
            f"{backup.get_created_at().printformat()}{palette.base}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            try:
                backup.restore(
                    incremental=incremental,
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
        backup.restore(
            incremental=incremental, source=source, verbosity_level=verbosity_level
        )

    print(
        f"Restored backup {backup.get_uuid()} (Created at: {backup.get_created_at()})"
    )

    return None


@click.command(
    "restore",
    help=f"Restore a {palette.sky}'BACKUP'{RESET} identified by its UUID or a "
    f"keyword ('latest', 'oldest' or 'largest', 'smallest') "
    f"to a {palette.sky}'BACKUP_SPACE'{RESET} identified by its UUID or name.",
)
@click.argument("backup_space", type=str, default=None, required=False)
@click.argument("backup", type=str, default=None, required=False)
@click.option(
    "--incremental",
    type=bool,
    default=True,
    help="Restore the backup "
    "incrementally. This means that only content, which is included in the backup "
    "will be affected. If this is 'False', the contents will be deleted and replaced "
    "by the backed up content.",
)
@click.option(
    "--source",
    "-s",
    type=click.Choice(["local", "remote"]),
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
    incremental: bool,
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

    if source == "remote" and backup.get_remote() is None:
        print_error_message(
            InvalidBackupError(
                f"The backup '{backup.get_uuid()}' does not have a remote backup file."
            ),
            debug=debug,
        )

    Console().print(backup.get_info_table())
    print(
        f"{palette.base}Restore mode: {palette.maroon}{'incremental' if incremental else 'non-incremental'}{RESET}"
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
                    incremental=incremental,
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
        backup.restore(
            incremental=incremental, source=source, force=force, verbosity_level=verbose
        )

    return None
