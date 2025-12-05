import rich_click as click

from backpy.cli.space.clear_command import clear
from backpy.cli.space.create_group import create
from backpy.cli.space.delete_command import delete
from backpy.cli.space.edit_group import edit
from backpy.cli.space.info_command import info
from backpy.cli.space.list_command import list_spaces


@click.group("space", help="Actions related to creating and managing backup spaces.")
def command():
    pass


command.add_command(create)
command.add_command(edit)
command.add_command(info)
command.add_command(list_spaces)
command.add_command(delete)
command.add_command(clear)
