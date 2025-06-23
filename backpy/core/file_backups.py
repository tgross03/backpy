import shutil
import time
import warnings
from datetime import timedelta
from pathlib import Path

from backpy import Backup, BackupSpace, BackupSpaceType, compression
from backpy.core.variables import VariableLibrary
from backpy.exceptions import InvalidBackupSpaceError, InvalidChecksumError


class FileBackupSpace(BackupSpace):
    def create_backup(
        self,
        comment: str = "",
        exclude: list[str] | None = None,
        verbosity_level: int = 1,
    ) -> Backup:

        if exclude is None:
            exclude = []

        backup = Backup.new(
            source_path=self._file_path,
            backup_space=self,
            comment=comment,
            exclude=list(set(exclude) | set(self._default_exclude)),
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

        backup = Backup.load_by_uuid(
            backup_space=self, unique_id=unique_id, fail_invalid=not force
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

        if not incremental:
            if verbosity_level >= 1:
                print("Mode is non-incremental -> Attempting to delete old files ...")

            was_dir = self._file_path.is_dir()

            shutil.rmtree(self._file_path)

            if was_dir:
                self._file_path.mkdir(exist_ok=True, parents=True)

        if from_remote:

            archive_path = Path(
                VariableLibrary().get_variable("paths.temporary_directory")
            )
            archive_path.mkdir(exist_ok=True, parents=True)
            archive_path /= backup.get_path().name

            if verbosity_level > 1:
                print(f"Creating temporary copy of remote archive at '{archive_path}'.")

            try:
                backup.get_remote().download(
                    source=backup.get_remote_archive_path(), target=archive_path
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
                f"Restored Backup with UUID '{unique_id}' from source {source}"
                f"at location {self._file_path}\n"
                f"Took {timedelta(seconds=time.time() - start_time).total_seconds()}"
                " seconds!"
            )

        if from_remote:
            if verbosity_level > 1:
                print(f"Removing temporary copy of remote archive '{archive_path}'.")

            archive_path.unlink()

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
        cls._default_exclude = cls._config["file_system.default_exclude"]

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
        cls._default_exclude = cls._config["file_system.default_exclude"]

        return cls

    @classmethod
    def new(
        cls,
        name: str,
        file_path: str,
        default_exclude: list[str] | None = None,
        **kwargs,
    ) -> "FileBackupSpace":
        parent = super(FileBackupSpace, cls).new(
            name=name, space_type=BackupSpaceType.from_name("FILE_SYSTEM"), **kwargs
        )
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        if isinstance(file_path, str):
            file_path = Path(file_path).expanduser()

        if default_exclude is None:
            default_exclude = []

        cls._file_path = file_path.absolute()
        cls._default_exclude = default_exclude

        cls._config["file_system.path"] = str(cls._file_path)
        cls._config["file_system.default_exclude"] = cls._default_exclude

        return cls
