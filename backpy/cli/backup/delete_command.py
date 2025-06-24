import click

from backpy import Backup, BackupSpace
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import BackupInput, BackupSpaceInput
from backpy.exceptions import InvalidBackupSpaceError

palette = get_default_palette()


def delete_interactive(verbosity_level: int):

    space = BackupSpaceInput(suggest_matches=True).prompt()
    backup = BackupInput(backup_space=space, suggest_matches=True).prompt()

    print(space.get_config())
    print(backup.get_config())


@click.command(
    "delete",
    help=f"Delete a {palette.sky}'BACKUP'{RESET} identified by its UUID or a "
    f"keyword ('latest' or 'oldest') "
    f"from a {palette.sky}'BACKUP_SPACE'{RESET} identified by its UUID or name.",
)
@click.argument("backup_space", type=str, default=None, required=False)
@click.argument("backup", type=str, default=None, required=False)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Sets the verbosity level of the output.",
)
@click.option(
    "--interactive", "-i", is_flag=True, help="Delete the backup in interactive mode."
)
def delete(
    backup_space: str | None,
    backup: str | None,
    verbose: int,
    interactive: bool,
) -> None:

    if interactive:
        return delete_interactive(verbosity_level=verbose)

    if backup_space is None or backup is None:
        raise ValueError(
            "If the '--interactive' flag is not given, you have to supply "
            "a valid value for the 'BACKUP_SPACE' and 'BACKUP' arguments."
        )

    try:
        space = BackupSpace.load_by_uuid(backup_space)
    except Exception:
        try:
            space = BackupSpace.load_by_name(backup_space)
        except Exception:
            raise InvalidBackupSpaceError(
                "There is no Backup Space with that name or UUID!"
            )

    space = space.get_type().child_class.load_by_uuid(unique_id=str(space.get_uuid()))

    backup = Backup.load_by_uuid(backup_space=space, unique_id=backup)
    backup.delete(verbosity_level=verbose)

    return None
