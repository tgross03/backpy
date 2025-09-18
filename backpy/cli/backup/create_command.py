import click

from backpy import BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import (
    BackupSpaceInput,
    EnumerationInput,
    TextInput,
    print_error_message,
)
from backpy.core.utils.exceptions import InvalidBackupSpaceError

palette = get_default_palette()


def create_interactive(verbosity_level: int) -> None:

    space = BackupSpaceInput(suggest_matches=True).prompt()

    def _validate_location(value: str):
        return value in ["all", "local", "remote"]

    if space.get_remote():
        location = TextInput(
            message=f"{palette.base}> Enter at which {palette.lavender}locations{palette.base} "
            f"the backup should be saved (options: 'all', 'remote', 'local'):{RESET}",
            validate=_validate_location,
            default_value="all",
            invalid_error_message=f"{palette.maroon}The given value is not one of the options "
            f"{palette.red}('all', 'remote', 'local'). "
            f"{palette.maroon}Please try again.{RESET}",
        ).prompt()
    else:
        location = "all"

    comment = TextInput(
        message=f"{palette.base}> Enter a {palette.lavender}custom comment{palette.base} "
        f"(can be empty):{RESET}",
        default_value="",
    ).prompt()

    if space.get_type().use_inclusion:
        include = EnumerationInput(
            message=f"{palette.base}> Enter a comma-seperated enumeration of {palette.lavender}"
            f"elements that should be {palette.maroon}included{palette.lavender} in the "
            f"backup{palette.base} "
            f"(e.g. paths, patterns, tables, databases) (if empty every non-excluded element "
            f"will be used):{RESET}",
            default_value="",
        ).prompt()
    else:
        include = []

    if space.get_type().use_exclusion:
        exclude = EnumerationInput(
            message=f"{palette.base}> Enter a comma-seperated enumeration of {palette.lavender}"
            f"elements that should be {palette.maroon}excluded{palette.lavender} from the "
            f"backup{palette.base} "
            f"(e.g. paths, patterns, tables, databases) (can be empty):{RESET}",
            default_value="",
        ).prompt()
    else:
        exclude = []

    space.create_backup(
        location=location,
        comment=comment,
        include=include,
        exclude=exclude,
        verbosity_level=verbosity_level,
    )


@click.command(
    "create",
    help=f"Create a new backup for a {palette.sky}'BACKUP_SPACE'{RESET} "
    f"identified by its UUID or name.",
)
@click.argument("backup_space", type=str, default=None, required=False)
@click.option(
    "--location",
    "-l",
    type=click.types.Choice(["all", "local", "remote"]),
    default="all",
    help="The location(s) to save the backup at.",
)
@click.option(
    "--comment",
    "-c",
    type=str,
    default="",
    help="A custom comment describing the backup contents.",
)
@click.option(
    "--include",
    "-I",
    type=str,
    multiple=True,
    default=None,
    help="A list of elements (e.g. paths, patterns, tables, databases) to include. "
    "If not set, every non-excluded element will be used backed up. "
    "Depending on the Backup Space this might not have an effect. "
    "Important: Symbols like ',' and '\"' have to be escaped!",
)
@click.option(
    "--exclude",
    "-X",
    type=str,
    multiple=True,
    default=None,
    help="A list of elements (e.g. paths, patterns, tables, databases) to exclude. "
    "Depending on the Backup Space this might not have an effect. "
    "Important: Symbols like ',' and '\"' have to be escaped!",
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
    "--interactive", "-i", is_flag=True, help="Create the backup in interactive mode."
)
def create(
    backup_space: str | None,
    location: str,
    comment: str,
    include: list[str],
    exclude: list[str],
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:

    verbose += 1

    if interactive:
        return create_interactive(verbosity_level=verbose)

    if backup_space is None:
        return print_error_message(
            InvalidBackupSpaceError(
                "If the '--interactive' flag is not given, you have to supply "
                "a valid value for the 'BACKUP_SPACE' argument."
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

    space = space.get_type().child_class.load_by_uuid(unique_id=str(space.get_uuid()))

    if not space.get_type().use_exclusion and exclude is not None:
        print(
            f"{palette.yellow}The Backup Space type {space.get_type().name} "
            "does not use exclusions. "
            f"The parameter has therefore no effect."
        )

    space.create_backup(
        location=location,
        comment=comment,
        include=include,
        exclude=exclude,
        verbosity_level=verbose,
    )

    return None
