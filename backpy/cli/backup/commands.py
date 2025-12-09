import rich_click as click

from backpy.cli.backup.create_command import create
from backpy.cli.backup.delete_command import delete
from backpy.cli.backup.info_command import info
from backpy.cli.backup.list_command import list_backups
from backpy.cli.backup.lock_command import lock
from backpy.cli.backup.restore_command import restore
from backpy.cli.backup.unlock_command import unlock


@click.group("backup", help="Actions related to creating and managing backups.")
def command():
    pass


command.add_command(create)
command.add_command(delete)
command.add_command(lock)
command.add_command(unlock)
command.add_command(restore)
command.add_command(info)
command.add_command(list_backups)
