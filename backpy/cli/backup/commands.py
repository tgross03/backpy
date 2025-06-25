import click

from backpy.cli.backup.create_command import create
from backpy.cli.backup.delete_command import delete
from backpy.cli.backup.info_commands import info


@click.group("backup", help="Actions related to creating and managing backups.")
def command():
    pass


command.add_command(create)
command.add_command(delete)
command.add_command(info)
