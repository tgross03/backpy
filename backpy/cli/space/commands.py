import click

from backpy.cli.space.create_group import create


@click.group("space", help="Actions related to creating and managing backup spaces.")
def command():
    pass


command.add_command(create)
