from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from backpy import BackupSpace


@dataclass
class BackupSpaceType:
    name: str
    description: str
    use_exclusion: bool
    child_class: Type[BackupSpace]

    @classmethod
    def from_name(cls, name):
        for backup_space_type in _get_backups_space_type():
            if backup_space_type.name == name:
                return backup_space_type
        return None


def _get_backups_space_type():
    from .file_backup_space import FileBackupSpace

    return [
        # BackupSpaceType(
        #     "SQL_DATABASE", "Backup-Space of an SQL-based database and its tables."
        # ),
        BackupSpaceType(
            "FILE_SYSTEM",
            "Backup-Space of one or more files and/or directories.",
            True,
            FileBackupSpace,
        ),
    ]
