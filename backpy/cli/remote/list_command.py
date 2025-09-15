import click

from backpy.cli.colors import get_default_palette

palette = get_default_palette()


@click.command(
    "list",
    help="",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Activate the debug log for the command "
    "to print full error traces in case of a problem.",
)
def list_remotes(debug: bool) -> None:
    pass
