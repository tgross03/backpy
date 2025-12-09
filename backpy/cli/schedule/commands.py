import rich_click as click

from backpy.cli.schedule.activate_command import activate
from backpy.cli.schedule.create_command import create
from backpy.cli.schedule.deactivate_command import deactivate
from backpy.cli.schedule.delete_command import delete
from backpy.cli.schedule.info_command import info
from backpy.cli.schedule.list_command import list_schedules


@click.group("schedule", help="Actions related to scheduling for automatic backups.")
def command():
    pass


command.add_command(create)
command.add_command(delete)
command.add_command(deactivate)
command.add_command(activate)
command.add_command(info)
command.add_command(list_schedules)
