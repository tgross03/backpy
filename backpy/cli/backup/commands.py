import click

from backpy.cli.backup.create_command import create
from backpy.cli.backup.delete_command import delete


@click.group("backup", help="Actions related to creating and managing backups.")
def command():
    pass


command.add_command(create)
command.add_command(delete)
