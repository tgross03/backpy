import click

from backpy import BackupSpace
from backpy.cli.colors import EFFECTS, RESET, get_default_palette
from backpy.cli.elements import EnumerationInput, TextInput
from backpy.exceptions import InvalidBackupSpaceError

palette = get_default_palette()


def create_interactive(verbosity_level: int) -> None:

    spaces = BackupSpace.get_backup_spaces()

    if len(spaces) == 0:
        print(
            f"{palette.red}There is no valid Backup Space present. "
            f"You have to create a Backup Space first. Use 'backpy --help' for help.{RESET}"
        )
        return

    space_names_uuids = []

    for space in spaces:
        space_names_uuids.append(str(space.get_uuid()))
        space_names_uuids.append(space.get_name())

    space = TextInput(
        message=f"{palette.base}> Enter the {palette.lavender}name{palette.base} "
        f"or {palette.lavender}UUID{palette.base} of the {EFFECTS.underline.on}"
        f"Backup Space{RESET}{palette.base}: ",
        invalid_error_message=f"{palette.red}There is no Backup Space with "
        f"{palette.maroon}name{palette.red} "
        f"or {palette.maroon}UUID {EFFECTS.reverse.on}{palette.yellow}"
        "{value}"
        f"{EFFECTS.reverse.off}"
        f"{palette.red}. Please try again!{RESET}",
        suggest_matches=True,
        suggestible_values=space_names_uuids,
    ).prompt()

    try:
        space = BackupSpace.load_by_uuid(space)
    except Exception:
        space = BackupSpace.load_by_name(space)

    space = space.get_type().child_class.load_by_uuid(unique_id=str(space.get_uuid()))

    def _validate_location(value: str):
        return value in ["all", "local", "remote"]

    if space.get_remote():
        location = TextInput(
            message=f"{palette.base}> Enter at which {palette.lavender}locations{palette.base} "
            f"the backup should be saved (options: 'all', 'remote', 'local'):{RESET}",
            validate=_validate_location,
            default_value="all",
            invalid_error_message=f"{palette.red}The given value is not one of the options "
            f"{palette.maroon}('all', 'remote', 'local'). "
            f"{palette.red}Please try again.{RESET}",
        ).prompt()
    else:
        location = "all"

    comment = TextInput(
        message=f"{palette.base}> Enter a {palette.lavender}custom comment{palette.base} "
        f"(can be empty):{RESET}",
        default_value="",
    ).prompt()

    if space.get_type().use_exclusion:
        exclude = EnumerationInput(
            message=f"{palette.base}> Enter an comma-seperated enumeration of {palette.lavender}"
            f"elements that should be excluded from the backup{palette.base} "
            f"(e.g. paths, patterns, tables, databases) (can be empty):{RESET}",
            default_value="",
        ).prompt()
    else:
        exclude = []

    space.create_backup(
        location=location,
        comment=comment,
        exclude=exclude,
        verbosity_level=verbosity_level,
    )


@click.command(
    "create",
    help="Create a new backup for a Backup Space identified by the UUID or name "
    "supplied in the argument 'BACKUP_SPACE'.",
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
    "--interactive", "-i", is_flag=True, help="Create the backup in interactive mode."
)
def create(
    backup_space: str | None,
    location: str,
    comment: str,
    exclude: list[str],
    verbose: int,
    interactive: bool,
) -> None:

    if interactive:
        return create_interactive(verbosity_level=verbose)

    if backup_space is None:
        raise ValueError(
            "If the '--interactive' flag is not given, you have to supply "
            "a valid value for the 'BACKUP_SPACE' argument."
        )

    try:
        space = BackupSpace.load_by_uuid(backup_space)
    except Exception:
        try:
            space = BackupSpace.load_by_name(backup_space)
        except Exception:
            raise InvalidBackupSpaceError(
                "There is no Backup Space with that name or UUID!"
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
        exclude=exclude,
        verbosity_level=verbose,
    )

    return None
