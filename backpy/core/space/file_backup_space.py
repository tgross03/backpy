from __future__ import annotations

import shutil
import time
import warnings
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from rich.table import Table

from backpy.core.backup import RestoreMode, compression
from backpy.core.config import VariableLibrary
from backpy.core.space.backup_space import BackupSpace
from backpy.core.utils.exceptions import (
    InvalidBackupError,
    InvalidBackupSpaceError,
    InvalidChecksumError,
)

if TYPE_CHECKING:
    from backpy.core.backup import Backup


class FileBackupSpace(BackupSpace):
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

        if exclude is None:
            exclude = []

        backup = Backup.new(
            source_path=self._file_path,
            backup_space=self,
            comment=comment,
            include=list(set(include) | set(self._default_include)),
            exclude=list(set(exclude) | set(self._default_exclude)),
            lock=lock,
            location=location,
            verbosity_level=verbosity_level,
        )

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
            backup_space=self,
            unique_id=unique_id,
            check_hash=False,
            fail_invalid=not force,
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

        if verbosity_level >= 1:
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

        start_time = time.time()

        if mode == RestoreMode.CLEAN:

            if backup.is_full_backup():
                if verbosity_level > 1:
                    print(
                        f"Restore mode is '{mode.name}' and is full backup ... Attempting to "
                        "delete all files ..."
                    )

                was_dir = self._file_path.is_dir()

                shutil.rmtree(self._file_path)

                if was_dir:
                    self._file_path.mkdir(exist_ok=True, parents=True)

            else:
                files, _ = compression.filter_paths(
                    root_path=self._file_path,
                    include=backup.get_include(),
                    exclude=backup.get_exclude(),
                )
                for file in files:
                    file.unlink(missing_ok=True)

        if from_remote:

            archive_path = Path(
                VariableLibrary.get_variable("paths.temporary_directory")
            )
            archive_path.mkdir(exist_ok=True, parents=True)
            archive_path /= backup.get_path().name

            if verbosity_level > 1:
                print(f"Creating temporary copy of remote archive at '{archive_path}'.")

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
            target_path=self._file_path,
            verbosity_level=verbosity_level,
        )

        if verbosity_level >= 1:
            print(
                f"Restored Backup with UUID '{unique_id}' from source {source} "
                f"at location {self._file_path}\n"
                f"Took {timedelta(seconds=time.time() - start_time).total_seconds()}"
                " seconds!"
            )

        if from_remote:
            if verbosity_level > 1:
                print(f"Removing temporary copy of remote archive '{archive_path}'.")

            archive_path.unlink()

    def get_info_table(self, verbosity_level: int = 1) -> Table:
        return super()._get_info_table(
            additional_info_idx=[3],
            additional_info={"Directory": self._file_path},
            verbosity_level=verbosity_level,
        )

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_uuid(cls, unique_id: str) -> "FileBackupSpace":

        parent = super(FileBackupSpace, cls).load_by_uuid(unique_id=unique_id)
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        if cls._type.name != "FILE_SYSTEM":
            raise InvalidBackupSpaceError(
                "The loaded BackupSpace is not a FileBackupSpace!"
            )

        cls._file_path = Path(cls._config["file_system.path"])

        return cls

    @classmethod
    def load_by_name(cls, name: str) -> "FileBackupSpace":

        parent = super(FileBackupSpace, cls).load_by_name(name=name)
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        if cls._type.name != "FILE_SYSTEM":
            raise InvalidBackupSpaceError(
                "The loaded BackupSpace is not a FileBackupSpace!"
            )

        cls._file_path = Path(cls._config["file_system.path"])

        return cls

    @classmethod
    def new(
        cls,
        name: str,
        file_path: str,
        **kwargs,
    ) -> "FileBackupSpace":

        from backpy.core.space import BackupSpaceType

        parent = super(FileBackupSpace, cls).new(
            name=name, space_type=BackupSpaceType.FILE_SYSTEM, **kwargs
        )
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        if isinstance(file_path, str):
            file_path = Path(file_path).expanduser()

        cls._file_path = file_path.absolute()
        cls._config["file_system.path"] = str(cls._file_path)

        return cls
