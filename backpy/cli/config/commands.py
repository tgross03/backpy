import rich_click as click

from backpy.cli.config.get_command import get_value
from backpy.cli.config.list_command import list_variables
from backpy.cli.config.reset_command import reset
from backpy.cli.config.set_command import set_value


@click.group("config", help="Actions related to configuring the package.")
def command():
    pass


command.add_command(get_value)
command.add_command(set_value)
command.add_command(list_variables)
command.add_command(reset)
