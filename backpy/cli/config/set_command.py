import rich_click as click
from fuzzyfinder import fuzzyfinder

from backpy import VariableLibrary
from backpy.cli.colors import EFFECTS, RESET, get_default_palette
from backpy.cli.elements import ConfirmInput, print_error_message
from backpy.core.utils.exceptions import InvalidTOMLConfigurationError

palette = get_default_palette()


@click.command(
    "set",
    help=f"Set the {palette.sky}'VALUE'{RESET} of a specific "
    f"configuration variable by its {palette.sky}'KEY'{RESET}.",
)
@click.argument("key", type=str, required=True)
@click.argument("value", type=str, required=True)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force the changing of the variable's value. This will skip the confirmation step.",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Activate the debug log for the command "
    "to print full error traces in case of a problem.",
)
def set_value(key: str, value: str, force: bool, debug: bool) -> None:
    try:
        prev_value = VariableLibrary.get_variable(key=key)

        if prev_value == value:
            print(
                f"{palette.red}ERROR: {palette.maroon}The variable is already set "
                f"to the given value.{RESET}"
            )
            return None

        if not force:
            confirm = ConfirmInput(
                message=f"{palette.base}> Are you sure you want to change the value "
                f"of the variable "
                f"{palette.sky}'{key}'{palette.base}?\n"
                f"Change: {palette.lavender}{prev_value} {palette.base}-> "
                f"{palette.green}{value}{RESET}\n",
                default_value=False,
            ).prompt()

            if confirm:
                VariableLibrary.set_variable(key=key, value=value)
            else:
                print(f"{palette.red}Canceled variable change.{RESET}")
                return None
        else:
            VariableLibrary.set_variable(key=key, value=value)

    except InvalidTOMLConfigurationError:
        return print_error_message(
            error=InvalidTOMLConfigurationError(
                "A severe problem occurred because the variable configuration could not be found! "
                "Use the 'backpy config regenerate' command to regenerate it."
            ),
            debug=debug,
        )
    except KeyError:
        matched = list(
            fuzzyfinder(
                key,
                VariableLibrary.get_config().get_keys(non_dict_only=True),
                highlight=True,
            )
        )
        return print_error_message(
            error=KeyError(
                f"The variable '{key}' could not be found!\n"
                f"Did you mean one of the following?{RESET}\n\n  {'\n  '.join(matched)}"
            ),
            debug=debug,
        )

    print("")
    print(
        f"{palette.base}Set {EFFECTS.bold.on}{palette.sky}{key}{RESET}{palette.overlay1} = "
        f"{palette.maroon}{value}{RESET}"
    )
    print("")

    return None
