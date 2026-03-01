from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from rich.table import Table

from backpy.core.database import MySQLDump, MySQLServer
from backpy.core.space.backup_space import BackupSpace
from backpy.core.utils.exceptions import InvalidBackupSpaceError

if TYPE_CHECKING:
    from backpy.core.backup import Backup

__all__ = ["MySQLBackupSpace"]


# databases: no dot in the string (e.g. "database1", "website" ...)
# tables: format `database.table` (e.g. "database1.table1", "website.users", ...)
# table data: format `database.table:data` (e.g. "database1.table1:data", "website.users:data", ...)
def _parse_exclusion_strings(
    exclude: list[str] | None,
) -> tuple[list[str], list[str], list[str]]:

    if exclude is None:
        return [], [], []

    databases = [x for x in exclude if "." not in x]
    tables = [x for x in exclude if "." in x and ":" not in x]
    table_data = [x for x in exclude if "." in x and ":" in x]

    return databases, tables, table_data


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

        from backpy.core.backup import Backup

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            dump_path = temp_dir / f"{self._uuid}.sql"

            exclude_databases, exclude_tables, exclude_table_data = (
                _parse_exclusion_strings(exclude)
            )

            self._dump.create(
                output_path=dump_path,
                server=self._server,
                exclude_databases=exclude_databases,
                exclude_tables=exclude_tables,
                exclude_table_data=exclude_table_data,
                overwrite=True,
                verbosity_level=verbosity_level,
            )

            backup = Backup.new(
                source_path=dump_path,
                backup_space=self,
                comment=comment,
                include=None,
                exclude=exclude,
                lock=lock,
                location=location,
                verbosity_level=verbosity_level,
            )

            return backup

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

        cls._server = MySQLServer.load_by_uuid(cls._config["database.uuid"])
        cls._dump = MySQLDump.from_dict(cls._config["database.dump"])

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

        cls._server = MySQLServer.load_by_uuid(cls._config["database.uuid"])
        cls._dump = MySQLDump.from_dict(cls._config["database.dump"])

        return cls

    @classmethod
    def new(
        cls,
        name: str,
        server: MySQLServer,
        dump: MySQLDump,
        **kwargs,
    ) -> "MySQLBackupSpace":

        from backpy.core.space import BackupSpaceType

        parent = super(MySQLBackupSpace, cls).new(
            name=name,
            space_type=BackupSpaceType.MYSQL_DATABASE,
            **kwargs,
        )
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        cls._server = server
        cls._config["database.uuid"] = str(server.get_uuid())

        cls._dump = dump
        cls._config["database.dump"] = dump.asdict()

        return cls
