from __future__ import annotations

from backpy.core.config import TOMLConfiguration
from backpy.core.config.variables import VariableLibrary

from rich import traceback

traceback.install(show_locals=True)

VariableLibrary()

__all__ = [
    "VariableLibrary",
    "TOMLConfiguration",
]
