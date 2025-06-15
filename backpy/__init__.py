from backpy.core.variables import VariableLibrary
from backpy.core.configuration import TOMLConfiguration

VariableLibrary()

from backpy.core import compression
from backpy.core.times import TimeObject

from backpy.core.remote import Remote, Protocol
from backpy.core.backup import Backup, BackupSpace, BackupSpaceType
from backpy.core.file_backups import FileBackupSpace

__all__ = [
    "VariableLibrary",
    "TOMLConfiguration",
    "FileBackupSpace",
    "BackupSpace",
    "BackupSpaceType",
    "Backup",
    "compression",
    "TimeObject",
    "Remote",
    "Protocol",
]
