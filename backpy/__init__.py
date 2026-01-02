from __future__ import annotations

from backpy.core.config import TOMLConfiguration
from backpy.core.config.variables import VariableLibrary

from backpy import version

from rich import traceback

traceback.install(show_locals=True)

VariableLibrary()

__all__ = [
    "VariableLibrary",
    "TOMLConfiguration",
]

__version__ = version.__version__
