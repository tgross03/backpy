import click

from backpy.cli.remote.create_command import create


@click.group("remote", help="Actions related to remote locations to save backups at.")
def command():
    pass


command.add_command(create)
