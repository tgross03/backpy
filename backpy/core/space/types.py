from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Type

from backpy.core.backup import RestoreMode
from backpy.core.space.file_backup_space import FileBackupSpace
from backpy.core.space.mysql_backup_space import MySQLBackupSpace
from backpy.core.utils.enum import Enum

if TYPE_CHECKING:
    from backpy.core.space import BackupSpace

__all__ = ["BackupSpaceType"]


@dataclass
class BackupSpaceTypeData:
    full_name: str
    description: str
    use_exclusion: bool
    use_inclusion: bool
    supported_restore_modes: list[RestoreMode]
    child_class: Type[BackupSpace]


class BackupSpaceType(BackupSpaceTypeData, Enum):

    MYSQL_DATABASE = (
        "MySQL/MariaDB Database Backup Space",
        "Backup-Space of a MariaDB or MySQL database and its tables.",
        True,
        True,
        [RestoreMode.OVERWRITE, RestoreMode.CLEAN],
        MySQLBackupSpace,
    )
    FILE_SYSTEM = (
        "File System Backup Space",
        "Backup-Space of one or more files and/or directories.",
        True,
        True,
        [
            RestoreMode.OVERWRITE,
            RestoreMode.CLEAN,
            RestoreMode.REPLACE,
            RestoreMode.MERGE,
        ],
        FileBackupSpace,
    )
