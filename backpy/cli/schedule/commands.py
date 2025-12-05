import rich_click as click

from backpy.cli.schedule.create_command import create


@click.group("schedule", help="Actions related to scheduling for automatic backups.")
def command():
    pass


command.add_command(create)
