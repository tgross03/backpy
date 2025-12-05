import rich_click as click

from backpy.cli.space.file_system.create_command import create_file_system


@click.group("create", help="Create backup spaces with different types.")
def create() -> None:
    pass


create.add_command(create_file_system)
