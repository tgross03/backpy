from typing import Callable

import click

from backpy.core.backup.types import BackupSpaceType


def common_options(space_type: BackupSpaceType) -> Callable:
    def decorator(func: Callable) -> Callable:
        func = click.argument(
            "backup_space",
            type=str,
            required=True,
        )(func)
        func = click.option(
            "--verbose",
            "-v",
            count=True,
            help="Sets the verbosity level of the output.",
        )(func)
        return func

    return decorator
