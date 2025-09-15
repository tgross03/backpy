from __future__ import annotations

from backpy.core.configuration import TOMLConfiguration
from backpy.core.variables import VariableLibrary

VariableLibrary()

from backpy.core import compression
from backpy.core.times import TimeObject
from backpy.core.remote import Remote, Protocol

# Import in the correct order to avoid circular imports
from backpy.core.types import BackupSpaceType
from backpy.core.backup_space import BackupSpace
from backpy.core.backup import Backup
from backpy.core.file_backup_space import FileBackupSpace

__all__ = [
    "FileBackupSpace",
    "TOMLConfiguration",
    "BackupSpace",
    "BackupSpaceType",
    "Backup",
    "compression",
    "TimeObject",
    "Remote",
    "Protocol",
]
