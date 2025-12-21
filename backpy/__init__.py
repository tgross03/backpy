from __future__ import annotations

from backpy.core.config.configuration import TOMLConfiguration
from backpy.core.config.variables import VariableLibrary

from rich import traceback

traceback.install(show_locals=True)

VariableLibrary()

from backpy.core.backup import compression
from backpy.core.utils.times import TimeObject
from backpy.core.remote import Remote, Protocol

# Import in the correct order to avoid circular imports
from backpy.core.space.types import BackupSpaceType
from backpy.core.space.backup_space import BackupSpace
from backpy.core.backup.backup import Backup
from backpy.core.space.file_backup_space import FileBackupSpace

__all__ = [
    "FileBackupSpace",
    "TOMLConfiguration",
    "VariableLibrary",
    "BackupSpace",
    "BackupSpaceType",
    "Backup",
    "compression",
    "TimeObject",
    "Remote",
    "Protocol",
]
