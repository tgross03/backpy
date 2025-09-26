import click

from backpy.cli.backup.create_command import create
from backpy.cli.backup.delete_command import delete
from backpy.cli.backup.info_command import info
from backpy.cli.backup.list_command import list_backups


@click.group("backup", help="Actions related to creating and managing backups.")
def command():
    pass


command.add_command(create)
command.add_command(delete)
command.add_command(info)
command.add_command(list_backups)
