import click

from backpy import BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import ConfirmInput, print_error_message
from backpy.core.backup.scheduling import Schedule
from backpy.core.utils.exceptions import InvalidBackupSpaceError

palette = get_default_palette()


def delete_interactive(force: bool, debug: bool, verbosity_level: int):
    pass


@click.command(
    "delete",
    help=f"Delete a {palette.sky}'SCHEDULE'{RESET} identified by its UUID. "
    f"Alternatively every schedule for a specific {palette.sky}'BACKUP_SPACE'{RESET}"
    f"can be deleted.",
)
@click.argument("schedule", type=str, default=None, required=False)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the deletion of the schedule. This will skip the confirmation step.",
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
    "--interactive", "-i", is_flag=True, help="Delete the schedule in interactive mode."
)
def delete(
    schedule: str | None,
    backup_space: str | None,
    force: bool,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:
    verbose += 1

    if interactive:
        return delete_interactive(force=force, debug=debug, verbosity_level=verbose)

    if schedule is None and backup_space is None:
        return print_error_message(
            ValueError(
                "If the '--interactive' flag is not given, you have to supply "
                "a valid value for the 'SCHEDULE' argument."
            ),
            debug=debug,
        )

    if schedule is not None and backup_space is not None:
        return print_error_message(
            ValueError("You have to either supply a 'SCHEDULE' or a 'BACKUP_SPACE'."),
            debug=debug,
        )

    if backup_space is not None:
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
        schedules = Schedule.load_by_backup_space(backup_space=space)
    else:
        try:
            schedules = [Schedule.load_by_uuid(schedule)]
        except Exception:
            return print_error_message(
                InvalidBackupSpaceError(
                    "There is no Backup Space with that name or UUID!"
                ),
                debug=debug,
            )

    schedule_str = "\n".join(
        [
            f"{palette.maroon}{schedule.get_uuid()} "
            f"(Description: {schedule.get_description()}"
            for schedule in schedules
        ]
    )

    if not force:
        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to delete the "
            f"{'schedule' if len(schedules) == 1 else 'schedules'} "
            f"{schedule_str}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            for schedule in schedules:
                schedule.delete(verbosity_level=verbose)
        else:
            print(
                f"{palette.red}Canceled removal of schedules "
                f"{palette.maroon}{schedule_str}{palette.red}.{RESET}"
            )
    else:
        schedule.delete(verbosity_level=verbose)

    print(f"Deleted schedules {schedule_str}.")

    return None
