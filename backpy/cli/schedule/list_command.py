import rich_click as click
from rich.console import Console
from rich.tree import Tree

from backpy import BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.core.backup import Schedule
from backpy.core.utils.exceptions import InvalidBackupSpaceError, InvalidScheduleError

palette = get_default_palette()


@click.command(
    "list",
    help="List all schedules.",
)
@click.option(
    "--backup-space",
    type=str,
    default=None,
    help="Backup space to list the schedules for",
)
@click.option("--active-only", is_flag=True, help="List only active schedules.")
@click.option(
    "--depth",
    type=int,
    default=1,
    help="The amount of details to show for each schedule. Default is 1.",
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
def list_schedules(
    backup_space: str | None,
    active_only: bool,
    depth: int,
    verbose: int,
    debug: bool,
) -> None:

    verbose += 1

    if backup_space is not None:
        try:
            space = BackupSpace.load_by_uuid(backup_space).get_as_child_class()
        except Exception:
            try:
                space = BackupSpace.load_by_name(backup_space).get_as_child_class()
            except Exception:
                return print_error_message(
                    InvalidBackupSpaceError(
                        "There is no Backup Space with that name or UUID!"
                    ),
                    debug=debug,
                )
        spaces = [space]
    else:
        spaces = BackupSpace.get_backup_spaces()

    schedules = []
    for space in spaces:
        schedules.extend(
            Schedule.load_by_backup_space(backup_space=space, active=active_only)
        )

    if len(schedules) == 0:
        if len(spaces) == 1:
            return print_error_message(
                error=InvalidScheduleError(
                    f"There are no {'active ' if active_only else ''}schedules "
                    f"for the selected backup space."
                ),
                debug=debug,
            )
        elif len(spaces) > 1:
            return print_error_message(
                error=InvalidScheduleError(
                    f"There are no {'active ' if active_only else ''}schedules created."
                ),
                debug=debug,
            )
        else:
            return print_error_message(
                error=InvalidBackupSpaceError("There are no backup spaces created.!"),
                debug=debug,
            )

    tree = Tree(f"{palette.mauve}Schedules{RESET}")

    for space in spaces:
        space_branch = tree.add(
            f"{palette.blue}{space.get_name()} (UUID: {space.get_uuid()}){RESET}",
        )

        for schedule in Schedule.load_by_backup_space(
            backup_space=space, active=active_only
        ):
            branch_suffix = (
                f" ({palette.green}active{palette.sky})"
                if schedule.is_active()
                else f" ({palette.red}inactive{palette.sky})"
            )
            schedule_branch = space_branch.add(
                f"{palette.sky}{schedule.get_uuid()}{branch_suffix if depth <= 1 else ''}{RESET}",
            )

            if depth > 1:
                schedule_branch.add(
                    f"{palette.lavender}Active: "
                    f"{palette.green if schedule.is_active() else palette.red}"
                    f"{schedule.is_active()}{RESET}"
                )
                schedule_branch.add(
                    f"{palette.lavender}Description: "
                    f"{palette.maroon}{schedule.get_description()}{RESET}"
                )
            if depth > 2:
                schedule_branch.add(
                    f"{palette.lavender}Time Pattern: "
                    f"{palette.maroon}{schedule.get_time_pattern()}{RESET}"
                )
            if depth > 3:
                schedule_branch.add(
                    f"{palette.lavender}Location: {palette.maroon}{schedule.get_location()}{RESET}"
                )
            if depth > 4:
                schedule_branch.add(
                    f"{palette.lavender}Include: {palette.maroon}{schedule.get_include()}{RESET}"
                )
                schedule_branch.add(
                    f"{palette.lavender}Exclude: {palette.maroon}{schedule.get_include()}{RESET}"
                )
            if depth > 5:
                schedule_branch.add(
                    f"{palette.lavender}Command: {palette.maroon}{schedule.get_command()}{RESET}"
                )

    Console().print(tree)

    return None
