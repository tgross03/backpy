import crontab
import rich_click as click
from crontab import CronSlices

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import (
    BackupSpaceInput,
    ConfirmInput,
    EnumerationInput,
    TextInput,
    print_error_message,
)
from backpy.core.backup import Schedule
from backpy.core.space import BackupSpace
from backpy.core.utils.exceptions import InvalidBackupSpaceError

palette = get_default_palette()


def create_interactive(verbosity_level: int, debug: bool) -> None:

    space = BackupSpaceInput(suggest_matches=True).prompt()

    def _validate_time(value: str) -> bool:
        if value is None:
            return False
        return (
            CronSlices.is_valid(value.split(" "))
            or value.removeprefix("@") in crontab.SPECIALS
        )

    time_pattern = TextInput(
        message=f"{palette.base}> Enter a {palette.lavender}time pattern{palette.base} following "
        f"which the schedule should be executed. The provided pattern has to be a valid "
        f"UNIX cron format pattern (e.g. '* */10 * * *' or '@hourly'):{RESET}",
        validate=_validate_time,
        invalid_error_message=f"{palette.maroon}The given value is not a valid UNIX cron "
        f"time pattern. Please try again.{RESET}",
    ).prompt()

    def _validate_location(value: str):
        return value in ["all", "local", "remote"]

    if space.get_remote() is not None:
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

    description = TextInput(
        message=f"{palette.base}> Enter a {palette.lavender}custom description{palette.base} "
        f"for the schedule (can be empty):{RESET}",
        default_value="",
    ).prompt()

    if space.get_type().use_inclusion:
        include = EnumerationInput(
            message=f"{palette.base}> Enter a comma-seperated enumeration of {palette.lavender}"
            f"elements that should be {palette.maroon}included{palette.lavender} in the "
            f"backups{palette.base} "
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
            f"backups{palette.base} "
            f"(e.g. paths, patterns, tables, databases) (can be empty):{RESET}",
            default_value="",
        ).prompt()
    else:
        exclude = []

    activate = ConfirmInput(
        message=f"{palette.base}> Should the schedule be activated after creation?{RESET}",
        default_value=True,
    ).prompt()

    schedule = Schedule.create_from_backup_space(
        backup_space=space,
        time_pattern=time_pattern,
        description=description,
        exclude=exclude,
        include=include,
        location=location,
        verbosity_level=verbosity_level,
    )

    if activate:
        try:
            schedule.activate()

            if verbosity_level > 1:
                print(f"Activated schedule '{schedule.get_uuid()}'.")

        except Exception as e:
            schedule.delete()
            print(
                f"Failed to activate schedule '{schedule.get_uuid()}'. Deleting schedule."
            )
            return print_error_message(error=e, debug=debug)

    if verbosity_level >= 1:
        activation_status = "active" if activate else "inactive"
        print(
            f"Created {activation_status} schedule {schedule.get_uuid()} for backup space "
            f"{space.get_uuid()}."
        )

    return None


@click.command(
    "create",
    help=f"Creates a schedule for a {palette.sky}BACKUP_SPACE{RESET} given a specific UNIX cron "
    f"{palette.sky}TIME_PATTERN{RESET}.",
)
@click.argument("backup_space", type=str, required=False)
@click.argument("time_pattern", type=str, required=False)
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
    "--location",
    "-l",
    type=click.types.Choice(["all", "local", "remote"]),
    default="all",
    help="The location(s) to save the backup at.",
)
@click.option(
    "--description", "-D", default="", help="The description of the schedule."
)
@click.option(
    "--activate",
    "-a",
    type=bool,
    default=True,
    help="Whether to activate the schedule after creation",
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
    "--interactive", "-i", is_flag=True, help="Create the schedule in interactive mode."
)
def create(
    backup_space: str,
    time_pattern: str,
    include: list[str],
    exclude: list[str],
    location: str,
    description: str,
    activate: bool,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:
    verbose += 1

    if interactive:
        return create_interactive(verbosity_level=verbose, debug=debug)

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

    if (
        not CronSlices.is_valid(time_pattern.split(" "))
        and not time_pattern.removeprefix("@") in crontab.SPECIALS
    ):
        return print_error_message(
            ValueError("The given value is not a valid UNIX cron time pattern."),
            debug=debug,
        )

    if not space.get_type().use_exclusion and exclude is not None:
        print(
            f"{palette.yellow}The Backup Space type {space.get_type().name} "
            "does not use exclusions. "
            f"The parameter has therefore no effect."
        )

    if not space.get_type().use_inclusion and include is not None:
        print(
            f"{palette.yellow}The Backup Space type {space.get_type().name} "
            "does not use inclusions. "
            f"The parameter has therefore no effect."
        )

    schedule = Schedule.create_from_backup_space(
        backup_space=space,
        time_pattern=time_pattern,
        include=include,
        exclude=exclude,
        location=location,
        description=description,
        verbosity_level=verbose,
    )

    if activate:
        try:
            schedule.activate()

            if verbose > 1:
                print(f"Activated schedule '{schedule.get_uuid()}'.")
        except Exception as e:
            schedule.delete()
            print(
                f"Failed to activate schedule '{schedule.get_uuid()}'. Deleting schedule."
            )
            return print_error_message(error=e, debug=debug)

    if verbose >= 1:
        activation_status = "active" if activate else "inactive"
        print(
            f"Created {activation_status} schedule {schedule.get_uuid()} for backup space "
            f"{space.get_uuid()}."
        )

    return None
