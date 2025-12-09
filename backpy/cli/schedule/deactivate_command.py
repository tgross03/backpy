import rich_click as click
from rich.console import Console

from backpy import BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import (
    BackupSpaceInput,
    ConfirmInput,
    ScheduleInput,
    print_error_message,
)
from backpy.core.backup.scheduling import Schedule
from backpy.core.utils.exceptions import InvalidBackupSpaceError, InvalidScheduleError

palette = get_default_palette()


def deactivate_interactive(force: bool, verbosity_level: int, debug: bool):

    schedule = ScheduleInput(suggest_matches=True, allow_none=True).prompt()

    if schedule is None:
        space = BackupSpaceInput(suggest_matches=True).prompt()
        schedules = Schedule.load_by_backup_space(backup_space=space, active=False)

        if schedules is None or len(schedules) == 0:
            return print_error_message(
                InvalidBackupSpaceError(
                    "There is no schedule assigned to the provided backup space!"
                ),
                debug=debug,
            )
    else:
        schedules = [schedule]

    schedule_str = "\n".join(
        [f"{palette.maroon}{schedule.get_uuid()}{RESET}" for schedule in schedules]
    )

    if not force:

        for schedule in schedules:
            Console().print(schedule.get_info_table())

        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to deactivate the "
            f"{'schedule' if len(schedules) == 1 else 'schedules'} "
            f"{schedule_str}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            for schedule in schedules:
                schedule.deactivate()
                print(
                    f"Deactivated schedule{'s' if len(schedules) > 1 else ''} {schedule_str}."
                )

        else:
            print(
                f"{palette.red}Canceled deactivation of schedules "
                f"{palette.maroon}{schedule_str}{palette.red}.{RESET}"
            )
    else:
        schedule.deactivate()
        print(f"Deactivated schedules {schedule_str}.")

    return None


@click.command(
    "deactivate",
    help=f"Deactivate a {palette.sky}'SCHEDULE'{RESET} identified by its UUID. "
    f"Alternatively every schedule for a specific {palette.sky}backup space{RESET} "
    "can be deactivated by not providing a schedule and instead providing the name or UUID of a "
    f"backup space to the {palette.sky}--backup-space{RESET} option.",
)
@click.argument("schedule", type=str, default=None, required=False)
@click.option("--backup-space", "-b", type=str, default=None, required=False)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the deactivation of the schedule. This will skip the confirmation step.",
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
    "--interactive",
    "-i",
    is_flag=True,
    help="Deactivate the schedule(s) in interactive mode.",
)
def deactivate(
    schedule: str | None,
    backup_space: str | None,
    force: bool,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:
    verbose += 1

    if interactive:
        return deactivate_interactive(force=force, verbosity_level=verbose, debug=debug)

    if schedule is None and backup_space is None:
        return print_error_message(
            ValueError(
                "You have to supply a valid value for the 'SCHEDULE' or 'BACKUP_SPACE' argument "
                "when not using interactive mode."
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

        if schedules is None or len(schedules) == 0:
            return print_error_message(
                InvalidBackupSpaceError(
                    "There is no schedule assigned to the provided backup space!"
                ),
                debug=debug,
            )
    else:
        try:
            schedules = [Schedule.load_by_uuid(schedule)]
        except Exception:
            return print_error_message(
                InvalidScheduleError("There is no Schedule with that UUID!"),
                debug=debug,
            )

    schedule_str = "\n".join(
        [f"{palette.maroon}{schedule.get_uuid()}{RESET}" for schedule in schedules]
    )

    if not force:

        for schedule in schedules:
            Console().print(schedule.get_info_table())

        confirm = ConfirmInput(
            message=f"{palette.base}Are you sure you want to deactivate the "
            f"{'schedule' if len(schedules) == 1 else 'schedules'} "
            f"{schedule_str}?{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            for schedule in schedules:
                schedule.deactivate()
                print(
                    f"Deactivated schedule{'s' if len(schedules) > 1 else ''} {schedule_str}."
                )

        else:
            print(
                f"{palette.red}Canceled deactivation of schedules "
                f"{palette.maroon}{schedule_str}{palette.red}.{RESET}"
            )
    else:
        schedule.deactivate()
        print(f"Deactivated schedules {schedule_str}.")

    return None
