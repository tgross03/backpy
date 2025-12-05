import rich_click as click

from backpy.cli.space.file_system.edit_command import edit_file_system


@click.group("edit", help="Edit backup spaces with different types.")
def edit() -> None:
    pass


edit.add_command(edit_file_system)
