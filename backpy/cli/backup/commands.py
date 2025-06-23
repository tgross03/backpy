import click

from backpy.cli.backup.create_command import create


@click.group("backup", help="Actions related to creating and managing backups.")
def command():
    pass


command.add_command(create)
