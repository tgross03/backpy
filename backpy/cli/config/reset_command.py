import rich_click as click

from backpy import VariableLibrary
from backpy.cli.colors import RESET, get_default_palette
from backpy.cli.elements import ConfirmInput

palette = get_default_palette()


@click.command(
    "reset",
    help="Reset the variable configuration of backpy to its default state.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the reset. This will skip the confirmation step.",
)
def reset(force: bool) -> None:

    if not force:
        confirm = ConfirmInput(
            message=f"{palette.maroon}> Are you sure you want to "
            f"{palette.red}reset{palette.maroon} "
            f"the entire variable configuration? "
            f"{palette.red}This cannot be undone!{RESET}",
            default_value=False,
        ).prompt()

        if confirm:
            VariableLibrary().generate(regenerate=True)
        else:
            print(f"{palette.red}Canceled reset.{RESET}")
            return None
    else:
        VariableLibrary().generate(regenerate=True)

    print(
        f"{palette.base}Regenerated variable configuration at "
        f"{palette.sky}{VariableLibrary.get_path()}{palette.base}.{RESET}"
    )

    return None
