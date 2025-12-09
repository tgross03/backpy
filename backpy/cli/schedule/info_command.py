import rich_click as click
from rich.console import Console

from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import ScheduleInput, print_error_message
from backpy.core.backup import Schedule
from backpy.core.utils.exceptions import InvalidScheduleError

palette = get_default_palette()


def info_interactive(include_command: bool, verbosity_level: int, debug: bool):
    schedule = ScheduleInput(suggest_matches=True).prompt()
    Console().print(schedule.get_info_table(include_command=include_command))

    return None


@click.command(
    "info",
    help=f"Get info about a {palette.sky}'SCHEDULE'{RESET} identified by its UUID.",
)
@click.argument("schedule", type=str, default=None, required=False)
@click.option(
    "--show-command",
    is_flag=True,
    help="Show the command that is saved in the Cronjob.",
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
    help="Get information about a schedule in interactive mode.",
)
def info(
    schedule: str,
    show_command: bool,
    verbose: int,
    debug: bool,
    interactive: bool,
) -> None:

    verbose += 1

    if interactive:
        return info_interactive(
            include_command=show_command, verbosity_level=verbose, debug=debug
        )

    if schedule is None:
        return print_error_message(
            ValueError(
                "If the '--interactive' flag is not given, you have to supply "
                "a valid value for the 'SCHEDULE' argument."
            ),
            debug=debug,
        )

    try:
        schedule_obj = Schedule.load_by_uuid(schedule)
    except InvalidScheduleError as e:
        return print_error_message(error=e, debug=debug)

    Console().print(schedule_obj.get_info_table(include_command=show_command))

    return None
