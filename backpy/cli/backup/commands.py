import click
from fuzzyfinder import fuzzyfinder

from backpy import BackupSpace
from backpy.cli.colors import EFFECTS, PALETTE, RESET

latte = PALETTE.latte


@click.group("backup", help="Actions related to creating and managing backups.")
def command():
    pass


def create_interactive() -> None:

    spaces = BackupSpace.get_backup_spaces()

    if len(spaces) == 0:
        print(
            f"{latte.red}There is no valid Backup Space present. "
            f"You have to create a Backup Space first. Use 'backpy --help' for help."
        )
        return

    space_names_uuids = []

    for space in spaces:
        space_names_uuids.append(str(space.get_uuid()))
        space_names_uuids.append(space.get_name())

    found_space = False

    space = None
    matched = []

    while not found_space:
        space = input(
            f"{latte.base}1. Enter the {latte.lavender}name{latte.base} "
            f"or {latte.lavender}UUID{latte.base} of the {EFFECTS.underline.on}"
            f"Backup Space{RESET}{latte.base}: "
        )

        matched = list(fuzzyfinder(space, space_names_uuids))

        if len(matched) == 0:
            print(
                f"{latte.red}There is no Backup Space with "
                f"{latte.maroon}name{latte.red} "
                f"or {latte.maroon}UUID {EFFECTS.reverse.on}{latte.yellow}"
                f"{space}{EFFECTS.reverse.off}"
                f"{latte.red}. Please try again!"
            )
            continue

        if matched[0] == space:
            break

        found_space = (
            input(
                f"{latte.base}Did you mean "
                f"{list(fuzzyfinder(space, space_names_uuids, highlight=True))[0]}"
                f"{latte.base}? (Y/n) "
            )
            or "Y"
        ).lower() == "y"

    space = matched[0]

    try:
        space = BackupSpace.load_by_uuid(space)
    except ValueError or NotADirectoryError:
        space = BackupSpace.load_by_name(space)

    print(space)


@click.command(
    "create",
    help="Create a new backup for a Backup Space identified by the UUID or name "
    "supplied in the argument 'BACKUP_SPACE'.",
)
@click.argument("backup_space", type=str, default=None, required=False)
@click.option(
    "--comment",
    "-c",
    type=str,
    default="",
    help="A custom comment describing the backup contents.",
)
@click.option(
    "--verbose",
    "-v",
    type=int,
    default=1,
    help="Sets the verbosity level of the output.",
)
@click.option(
    "--interactive", "-i", is_flag=True, help="Create the backup in interactive mode."
)
def create(
    backup_space: str | None, comment: str, verbose: int, interactive: bool
) -> None:

    if interactive:
        return create_interactive()

    if backup_space is None:
        raise ValueError(
            "If the '--interactive' flag is not given, you have to supply "
            "a valid value for the 'BACKUP_SPACE' argument."
        )

    return None


command.add_command(create)
