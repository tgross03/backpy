from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from backpy.core.space import BackupSpace


@dataclass
class BackupSpaceType:
    name: str
    full_name: str
    description: str
    use_exclusion: bool
    use_inclusion: bool
    child_class: Type[BackupSpace]

    @classmethod
    def from_name(cls, name):
        for backup_space_type in get_backup_space_types():
            if backup_space_type.name == name:
                return backup_space_type
        return None


def get_backup_space_types() -> list[BackupSpaceType]:
    from backpy.core.space.file_backup_space import FileBackupSpace

    return [
        # BackupSpaceType(
        #     "SQL_DATABASE", "Backup-Space of a MariaDB or MySQL database and its tables."
        # ),
        BackupSpaceType(
            name="FILE_SYSTEM",
            full_name="File System Backup Space",
            description="Backup-Space of one or more files and/or directories.",
            use_inclusion=True,
            use_exclusion=True,
            child_class=FileBackupSpace,
        ),
    ]
