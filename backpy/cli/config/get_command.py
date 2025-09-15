import click
from fuzzyfinder import fuzzyfinder
from rich.console import Console
from rich.tree import Tree

from backpy import VariableLibrary
from backpy.cli.colors import EFFECTS, RESET, get_default_palette
from backpy.cli.elements import print_error_message
from backpy.exceptions import InvalidTOMLConfigurationError

palette = get_default_palette()


@click.command(
    "get",
    help=f"Get the value of a specific configuration variable by its {palette.sky}'KEY'{RESET}.",
)
@click.argument("key", type=str, required=True)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Activate the debug log for the command "
    "to print full error traces in case of a problem.",
)
def get_value(key: str, debug: bool) -> None:
    try:
        value = VariableLibrary().get_variable(key=key)
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
                VariableLibrary().get_config().get_keys(non_dict_only=True),
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
    if not isinstance(value, dict):
        print(
            f"{EFFECTS.bold.on}{palette.sky}{key}{RESET}{palette.overlay1} = "
            f"{palette.maroon}{value}{RESET}"
        )
    else:

        def render_tree(d, tree):
            for k, v in d.items():
                if isinstance(v, dict):
                    branch = tree.add(f"{EFFECTS.bold.on}{palette.blue}{k}{RESET}")
                    render_tree(v, branch)
                else:
                    tree.add(
                        f"{palette.sky}{k}{RESET}{palette.overlay1} = {palette.maroon}{v}{RESET}"
                    )

        console = Console()
        root = Tree(
            f"{palette.mauve}{'Variable Configuration' if key is None else key}{RESET}"
        )
        render_tree(value, root)
        console.print(root)
    print("")

    return None
