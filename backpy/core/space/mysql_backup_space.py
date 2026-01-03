from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.table import Table

from backpy.core.encryption.password import encrypt
from backpy.core.space.backup_space import BackupSpace
from backpy.core.utils.exceptions import InvalidBackupSpaceError

if TYPE_CHECKING:
    from backpy.core.backup import Backup


class MySQLBackupSpace(BackupSpace):
    def create_backup(
        self,
        comment: str = "",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        lock: bool = False,
        location: str = "all",
        verbosity_level: int = 1,
    ) -> Backup:
        pass

    def restore_backup(
        self,
        unique_id: str,
        incremental: bool,
        source: str = "local",
        force: bool = False,
        verbosity_level: int = 1,
    ) -> None:
        pass

    def get_info_table(self, verbosity_level: int = 1) -> Table:
        return super()._get_info_table(
            additional_info_idx=[3],
            additional_info={},
            verbosity_level=verbosity_level,
        )

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_uuid(cls, unique_id: str) -> "MySQLBackupSpace":

        parent = super(MySQLBackupSpace, cls).load_by_uuid(unique_id=unique_id)
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        if cls._type.name != "MySQL_DATABASE":
            raise InvalidBackupSpaceError(
                "The loaded BackupSpace is not a MySQLBackupSpace!"
            )

        cls._file_path = Path(cls._config["file_system.path"])

        return cls

    @classmethod
    def load_by_name(cls, name: str) -> "MySQLBackupSpace":

        parent = super(MySQLBackupSpace, cls).load_by_name(name=name)
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        if cls._type.name != "MySQL_DATABASE":
            raise InvalidBackupSpaceError(
                "The loaded BackupSpace is not a MySQLBackupSpace!"
            )

        cls._file_path = Path(cls._config["file_system.path"])

        return cls

    @classmethod
    def new(
        cls,
        name: str,
        hostname: str,
        port: int,
        username: str,
        password: str,
        databases: list[str],
        tables: list[str],
        **kwargs,
    ) -> "MySQLBackupSpace":

        from backpy.core.space import BackupSpaceType

        parent = super(MySQLBackupSpace, cls).new(
            name=name,
            space_type=BackupSpaceType.from_name("MySQLBackupSpace"),
            **kwargs,
        )
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        cls._hostname = hostname
        cls._config["mysql.hostname"] = hostname
        cls._port = port
        cls._config["mysql.port"] = port
        cls._username = username
        cls._config["mysql.username"] = username
        cls._password = password
        cls._config["mysql.password"] = encrypt(password)
        cls._databases = databases
        cls._config["mysql.databases"] = tables
        cls._tables = tables
        cls._config["mysql.tables"] = tables

        return cls
