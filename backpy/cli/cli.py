import sys
from datetime import datetime
from pathlib import Path

import click

import backpy
import backpy.version
from backpy import TOMLConfiguration
from backpy.cli.colors import EFFECTS, PALETTE, RESET

from .backup import commands as backup
from .config import commands as config
from .schedule import commands as schedule
from .space import commands as space

latte = PALETTE.latte


def _print_version(ctx, param, value):

    if not value or ctx.resilient_parsing:
        return

    version = backpy.version.version

    content = f"🐍 backpy ◆ v{version}"
    frame_width = len(content) + 2

    print(f"{latte.sky}{'─' * frame_width}{RESET}")
    print(
        f" {EFFECTS.bold.on}{latte.maroon}🐍 backpy{RESET} {latte.yellow}◆{RESET} "
        f"{EFFECTS.bold.on}{latte.green}v{version}{RESET} "
    )
    print(f"{latte.sky}{'─' * frame_width}{RESET}")

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
            f"{latte.base}For more information on this package visit "
            f"{EFFECTS.bold.on}{EFFECTS.underline.on}{latte.blue}{docu_url}{RESET}!\n\n"
            f"Version {latte.green}{version}{RESET}"
        )
    else:
        return (
            f"{latte.overlay1}©️{RESET} {EFFECTS.bold.on}{latte.yellow}"
            f"{year_str}{year}{RESET}, "
            f"{EFFECTS.bold.on}{latte.maroon}{authors}{RESET}\n\n"
            + f"🐍 {latte.base}backpy version {EFFECTS.bold.on}{latte.green}"
            f"v{version}{RESET}\n\n"
            + f"📦 {latte.base}The code repository for this Python package "
            f"is available under "
            f"{EFFECTS.bold.on}{EFFECTS.underline.on}{latte.sky}{repo_url}{RESET}.\n\n"
            + f"📚 {latte.base}For more information on this package visit "
            f"{EFFECTS.bold.on}{EFFECTS.underline.on}{latte.blue}{docu_url}{RESET}!\n\n"
            + f"⚖️ {latte.base}This package is licensed under the "
            f"{EFFECTS.bold.on}{latte.green}{lic['text']}{RESET} {latte.base}license. "
            + f"More information on this license can be found under "
            f"{EFFECTS.bold.on}{EFFECTS.underline.on}{latte.sky}{lic['url']}{RESET}."
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
entry_point.add_command(backup.command)
entry_point.add_command(schedule.command)
entry_point.add_command(config.command)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        entry_point.main(["--help"])
    entry_point()
