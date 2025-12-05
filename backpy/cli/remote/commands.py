import rich_click as click

from backpy.cli.remote.create_command import create
from backpy.cli.remote.delete_command import delete
from backpy.cli.remote.edit_command import edit
from backpy.cli.remote.info_command import info
from backpy.cli.remote.list_command import list_remotes
from backpy.cli.remote.test_command import test


@click.group("remote", help="Actions related to remote locations to save backups at.")
def command():
    pass


command.add_command(create)
command.add_command(edit)
command.add_command(delete)
command.add_command(list_remotes)
command.add_command(info)
command.add_command(test)
