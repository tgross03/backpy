import sys
from datetime import datetime
from pathlib import Path

import rich_click as click

import backpy
import backpy.version
from backpy import TOMLConfiguration, VariableLibrary
from backpy.cli.colors import EFFECTS, RESET, get_default_palette

from .backup import commands as backup
from .config import commands as config
from .remote import commands as remote
from .schedule import commands as schedule
from .space import commands as space

palette = get_default_palette()

click.rich_click.THEME = (
    f"{VariableLibrary.get_variable('cli.rich.palette')}-"
    f"{VariableLibrary.get_variable('cli.rich.style')}"
)


def _print_version(ctx, param, value):

    if not value or ctx.resilient_parsing:
        return

    version = backpy.version.version

    content = f"🐍 backpy ◆ v{version}"
    frame_width = len(content) + 2

    print(f"{palette.sky}{'─' * frame_width}{RESET}")
    print(
        f" {EFFECTS.bold.on}{palette.maroon}🐍 backpy{RESET} {palette.yellow}◆{RESET} "
        f"{EFFECTS.bold.on}{palette.green}v{version}{RESET} "
    )
    print(f"{palette.sky}{'─' * frame_width}{RESET}")

    ctx.exit()


def _print_info(ctx, param, value):

    if not value or ctx.resilient_parsing:
        return

    print(_create_epilog(short=False))

    ctx.exit()


def _create_epilog(short):
    pyproject = TOMLConfiguration(
        Path(backpy.__file__).parent.parent / "pyproject.toml"
    )
    authors = pyproject["project.authors"]
    authors = ",".join([author["name"] for author in authors])
    lic = pyproject["project.license"]
    repo_url = pyproject["project.urls.Repository"]
    docu_url = pyproject["project.urls.Documentation"]
    year = datetime.now().year

    version = backpy.version.version

    year_str = "2025 - " if year != 2025 else ""

    if short:
        return (
            f"{palette.base}For more information on this package visit "
            f"{EFFECTS.bold.on}{EFFECTS.underline.on}{palette.blue}{docu_url}{RESET}!\n\n"
            f"Version {palette.green}{version}{RESET}"
        )
    else:
        return (
            f"{palette.overlay1}©️{RESET} {EFFECTS.bold.on}{palette.yellow}"
            f"{year_str}{year}{RESET}, "
            f"{EFFECTS.bold.on}{palette.maroon}{authors}{RESET}\n\n"
            + f"🐍 {palette.base}backpy version {EFFECTS.bold.on}{palette.green}"
            f"v{version}{RESET}\n\n"
            + f"📦 {palette.base}The code repository for this Python package "
            f"is available under "
            f"{EFFECTS.bold.on}{EFFECTS.underline.on}{palette.sky}{repo_url}{RESET}.\n\n"
            + f"📚 {palette.base}For more information on this package visit "
            f"{EFFECTS.bold.on}{EFFECTS.underline.on}{palette.blue}{docu_url}{RESET}!\n\n"
            + f"⚖️ {palette.base}This package is licensed under the "
            f"{EFFECTS.bold.on}{palette.green}{lic['text']}{RESET} {palette.base}license. "
            + f"More information on this license can be found under "
            f"{EFFECTS.bold.on}{EFFECTS.underline.on}{palette.sky}{lic['url']}{RESET}."
        )


# Structure of the entry_point group and adding of the subcommands
# taken from https://stackoverflow.com/a/39228156
@click.group(epilog=_create_epilog(short=True))
@click.option(
    "--version",
    "-v",
    is_flag=True,
    is_eager=True,
    callback=_print_version,
    help="Displays the current version of backpy.",
)
@click.option(
    "--info",
    is_flag=True,
    is_eager=False,
    callback=_print_info,
    help="Displays some information about backpy.",
)
def entry_point(**kwargs):
    pass


entry_point.add_command(space.command)
entry_point.add_command(remote.command)
entry_point.add_command(backup.command)
entry_point.add_command(schedule.command)
entry_point.add_command(config.command)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        entry_point.main(["--help"])
    entry_point()
