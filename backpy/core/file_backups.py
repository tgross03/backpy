import shutil
import time
import warnings
from datetime import timedelta
from pathlib import Path

from backpy import Backup, BackupSpace, BackupSpaceType, compression


class FileBackupSpace(BackupSpace):
    def __init__(self, file_path: Path, default_exclude: list[str], **kwargs):
        super().__init__(space_type=BackupSpaceType.from_name("FILE_SYSTEM"), **kwargs)
        self._file_path: Path = file_path
        self._default_exclude: list[str] = default_exclude

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
        force: bool = False,
        verbosity_level: int = 1,
    ) -> None:

        backup = Backup.load_by_uuid(
            backup_space=self, unique_id=unique_id, fail_invalid=not force
        )

        if not backup.check_hash() and force:
            raise warnings.warn(
                "Forcing restore of possibly corrupted "
                f"backup '{backup.get_uuid()}'. This can lead "
                f"to unwanted behavior."
            )

        if verbosity_level >= 1:
            print(f"Restoring backup '{backup.get_uuid()}' ...")

        start_time = time.time()

        if not incremental:
            if verbosity_level >= 1:
                print("Mode is non-incremental -> Attempting to delete old files ...")

            was_dir = self._file_path.is_dir()

            shutil.rmtree(self._file_path)

            if was_dir:
                self._file_path.mkdir(exist_ok=True, parents=True)

        compression.unpack(
            archive_path=backup.get_path(),
            target_path=self._file_path,
            verbosity_level=verbosity_level,
        )

        if verbosity_level >= 1:
            print(
                f"Restored Backup with UUID '{unique_id}' "
                f"at location {self._file_path}\n"
                f"Took {timedelta(seconds=time.time() - start_time).total_seconds()}"
                " seconds!"
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
            raise TypeError("The loaded BackupSpace is not a FileBackupSpace!")

        cls._file_path = Path(cls._config["file_system.path"])
        cls._default_exclude = list[str] = cls._config["file_system.default_exclude"]

        return cls

    @classmethod
    def load_by_name(cls, name: str) -> "FileBackupSpace":

        parent = super(FileBackupSpace, cls).load_by_name(name=name)
        cls = cls.__new__(cls)
        cls.__dict__.update(parent.__dict__)

        if cls._type.name != "FILE_SYSTEM":
            raise TypeError("The loaded BackupSpace is not a FileBackupSpace!")

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

        if isinstance(file_path, str):
            file_path = Path(file_path)

        if default_exclude is None:
            default_exclude = []

        cls = BackupSpace.new(
            name=name, space_type=BackupSpaceType.from_name("FILE_SYSTEM"), **kwargs
        )
        cls._file_path = file_path.absolute()
        cls._default_exclude = default_exclude

        cls._config["file_system.path"] = str(cls._file_path)
        cls._config["file_system.default_exclude"] = cls._default_exclude

        return cls
