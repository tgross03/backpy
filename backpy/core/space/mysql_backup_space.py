from __future__ import annotations

import tempfile
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from rich.table import Table

from backpy import VariableLibrary
from backpy.core.backup import RestoreMode, compression
from backpy.core.database import MySQLDump, MySQLServer
from backpy.core.space.backup_space import BackupSpace
from backpy.core.utils.exceptions import (
    InvalidBackupError,
    InvalidBackupSpaceError,
    InvalidChecksumError,
)

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

            backup_dir = temp_dir / str(self._uuid)

            exclude_databases, exclude_tables, exclude_table_data = (
                _parse_exclusion_strings(exclude)
            )

            common_args = dict(
                server=self._server,
                exclude_databases=exclude_databases,
                exclude_tables=exclude_tables,
                exclude_table_data=exclude_table_data,
                overwrite=True,
                verbosity_level=verbosity_level,
            )

            replace_path = temp_dir / "replace.sql"
            self._dump.create(
                output_path=replace_path,
                replace_data=True,
                insert_ignore=False,
                **common_args,
            )

            insert_path = temp_dir / "insert.sql"
            self._dump.create(
                output_path=insert_path,
                replace_data=False,
                insert_ignore=True,
                **common_args,
            )

            backup = Backup.new(
                source_path=backup_dir,
                backup_space=self,
                comment=comment,
                include=None,
                exclude=exclude,
                lock=lock,
                location=location,
                verbosity_level=verbosity_level,
            )

            # TODO: Add dump info to backup config

            return backup

    def restore_backup(
        self,
        unique_id: str,
        mode: RestoreMode,
        source: str = "local",
        force: bool = False,
        verbosity_level: int = 1,
    ) -> None:

        from backpy.core.backup import Backup

        backup = Backup.load_by_uuid(
            unique_id=unique_id, backup_space=self, verbosity_level=verbosity_level
        )

        if source == "remote" and not backup.has_remote_archive():
            raise InvalidBackupError(
                f"The backup '{backup.get_uuid()}' does not have a remote backup file."
            )
        elif source == "local" and not backup.has_local_archive():
            raise InvalidBackupError(
                f"The backup '{backup.get_uuid()}' does not have a local backup file."
            )

        from_remote = source == "remote"

        if verbosity_level > 1:
            print(f"Restoring backup '{backup.get_uuid()}' ...")

        if not backup.check_hash(remote=from_remote):
            if force:
                warnings.warn(
                    "Forcing restore of possibly corrupted "
                    f"backup '{backup.get_uuid()}'. This can lead "
                    f"to unwanted behavior."
                )
            else:
                raise InvalidChecksumError(
                    "The backup could not be restored,"
                    "because its SHA256 sum could not be verified. "
                    "Use --force / -f flag to force the restoring."
                )

        # start_time = time.time()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            if from_remote:

                archive_path = Path(
                    VariableLibrary.get_variable("paths.temporary_directory")
                )
                archive_path.mkdir(exist_ok=True, parents=True)
                archive_path /= backup.get_path().name

                if verbosity_level > 1:
                    print(
                        f"Creating temporary copy of remote archive at '{archive_path}'."
                    )

                try:
                    with backup.get_remote()(context_verbosity=verbosity_level):
                        backup.get_remote().download(
                            source=backup.get_remote_archive_path(),
                            check_hash=True,
                            target=archive_path,
                        )
                except InvalidChecksumError:
                    if force:
                        warnings.warn(
                            "Forcing restore of possibly corrupted "
                            f"backup '{backup.get_uuid()}'. This can lead "
                            f"to unwanted behavior."
                        )
                    else:
                        raise InvalidChecksumError(
                            "The backup could not be restored,"
                            "because its SHA256 sum could not be verified. "
                            "Use --force / -f flag to force the restoring."
                        )
            else:
                archive_path = backup.get_path()

            compression.unpack(
                archive_path=archive_path,
                target_path=temp_dir,
                verbosity_level=verbosity_level,
            )

            if mode == RestoreMode.CLEAN:
                # If multiple databases
                if self._dump:
                    pass

            if from_remote:
                if verbosity_level > 1:
                    print(
                        f"Removing temporary copy of remote archive '{archive_path}'."
                    )
                archive_path.unlink()

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
