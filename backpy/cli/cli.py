import sys
from datetime import datetime
from pathlib import Path

import click

import backpy
import backpy.version
from backpy import TOMLConfiguration

from .backup import commands as backup
from .config import commands as config
from .schedule import commands as schedule
from .space import commands as space

# file structure based on https://stackoverflow.com/a/39228156


# ANSI color codes
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
GRAY = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"


def _print_version(ctx, param, value):

    if not value or ctx.resilient_parsing:
        return

    version = backpy.version.version

    content = f"🐍 backpy ◆ v{version}"
    frame_width = len(content) + 2

    print(f"{CYAN}{'─' * frame_width}{RESET}")
    print(
        f" {BOLD}{MAGENTA}🐍 backpy{RESET} {YELLOW}◆{RESET} "
        f"{BOLD}{GREEN}v{version}{RESET} "
    )
    print(f"{CYAN}{'─' * frame_width}{RESET}")

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
            f"{WHITE}For more information on this package visit "
            f"{BOLD}{UNDERLINE}{BLUE}{docu_url}{RESET}!\n\n"
            f"Version {GREEN}{version}{RESET}"
        )
    else:
        return (
            f"{GRAY}©️{RESET} {BOLD}{YELLOW}{year_str}{year}{RESET}, "
            f"{BOLD}{MAGENTA}{authors}{RESET}\n\n"
            + f"🐍 {WHITE}backpy version {BOLD}{GREEN}v{version}{RESET}\n\n"
            + f"📦 {WHITE}The code repository for this Python package "
            f"is available under "
            f"{BOLD}{UNDERLINE}{CYAN}{repo_url}{RESET}.\n\n"
            + f"📚 {WHITE}For more information on this package visit "
            f"{BOLD}{UNDERLINE}{BLUE}{docu_url}{RESET}!\n\n"
            + f"⚖️ {WHITE}This package is licensed under the "
            f"{BOLD}{GREEN}{lic['text']}{RESET} {WHITE}license. "
            + f"More information on this license can be found under "
            f"{BOLD}{UNDERLINE}{CYAN}{lic['url']}{RESET}."
        )


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
