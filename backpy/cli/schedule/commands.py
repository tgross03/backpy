import click

from backpy.cli.schedule.create_command import create
from backpy.cli.schedule.list_command import list_backups


@click.group("schedule", help="Actions related to scheduling for automatic backups.")
def command():
    pass


command.add_command(create)
