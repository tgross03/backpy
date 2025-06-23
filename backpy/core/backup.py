from __future__ import annotations

import shutil
import time
import uuid
import warnings
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from mergedeep import merge

from backpy import Remote, TimeObject, TOMLConfiguration, compression
from backpy.core.utils import _calculate_sha256sum
from backpy.exceptions import InvalidBackupError, InvalidChecksumError

if TYPE_CHECKING:
    from backpy import BackupSpace


class Backup:
    def __init__(
        self,
        path: Path,
        backup_space: BackupSpace,
        unique_id: uuid.UUID,
        sha256sum: str,
        comment: str,
        created_at: TimeObject,
        remote: Remote | None,
    ):
        self._path: Path = path
        self._backup_space: BackupSpace = backup_space
        self._uuid: uuid.UUID = unique_id
        self._hash: str = sha256sum
        self._comment: str = comment
        self._created_at: TimeObject = created_at
        self._remote: Remote | None = remote
        self._config: TOMLConfiguration = TOMLConfiguration(
            path.parent / (str(unique_id) + ".toml")
        )

    def calculate_hash(self) -> str:
        return _calculate_sha256sum(self._path)

    def check_hash(self, remote=False) -> bool:
        if remote:
            return (
                self._remote.get_hash(target=self.get_remote_archive_path())
                == self._hash
            )
        else:
            return self.calculate_hash() == self._hash

    def delete(self, verbosity_level: int = 1) -> None:

        start_time = time.time()

        self._config.get_path().unlink()
        self._path.unlink()

        if self._remote:
            self._remote.remove(
                target=self.get_remote_archive_path(), verbosity_level=verbosity_level
            )
            self._remote.remove(
                target=self.get_remote_config_path(), verbosity_level=verbosity_level
            )

        if verbosity_level >= 1:
            print(
                f"Deleted backup with UUID '{self._uuid}'.\n"
                f"Took {timedelta(seconds=time.time() - start_time).total_seconds()} "
                "seconds."
            )

    def update_config(self):
        current_content = self._config.as_dict()

        content = {
            "uuid": str(self._uuid),
            "backup_space": str(self._backup_space.get_uuid()),
            "hash": self._hash,
            "comment": self._comment,
            "created_at": self._created_at.isoformat(),
            "remote": str(self._remote.get_uuid()),
        }

        self._config.dump_dict(dict(merge({}, content, current_content)))

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_uuid(
        cls, backup_space: BackupSpace, unique_id: str, fail_invalid: bool = False
    ):

        unique_id = uuid.UUID(unique_id)

        path = backup_space.get_backup_dir() / (
            str(unique_id) + backup_space.get_compression_algorithm().extension
        )

        if not path.exists():
            raise InvalidBackupError(
                f"The Backup with UUID '{unique_id}' does not exist."
            )

        config = TOMLConfiguration(
            backup_space.get_backup_dir() / (str(unique_id) + ".toml")
        )

        if not config.is_valid():
            raise InvalidBackupError(
                f"The Backup with UUID '{unique_id}' could not be loaded because its"
                "'config.toml' is invalid or missing!"
            )

        cls = cls(
            path=path,
            backup_space=backup_space,
            unique_id=unique_id,
            sha256sum=config["hash"],
            comment=config["comment"],
            created_at=TimeObject.fromisoformat(config["created_at"]),
            remote=Remote.load_by_uuid(config["remote"]),
        )

        if not cls.check_hash():
            err_msg = (
                f"The SHA256 of the loaded backup with UUID '{unique_id}' "
                "is not identical with the one saved in its configuration. "
                "This could mean, that the file is corrupted or was changed."
            )
            if not fail_invalid:
                warnings.warn(err_msg)
            else:
                raise InvalidChecksumError(err_msg)

        return cls

    @classmethod
    def new(
        cls,
        source_path: Path,
        backup_space: BackupSpace,
        comment: str = "",
        exclude: list[str] | None = None,
        verbosity_level: int = 1,
    ):

        if not source_path.exists(follow_symlinks=True):
            raise FileNotFoundError(
                "The given source path could not be found at path "
                f"'{source_path.absolute()}'!"
            )

        start_time = time.time()

        if exclude is None:
            exclude = []

        unique_id = uuid.uuid4()
        created_at = TimeObject.localnow()

        if verbosity_level >= 1:
            print(f"Creating Backup with UUID '{unique_id}'...")

        archive_path = compression.compress(
            root_path=source_path,
            archive_name=str(unique_id),
            fmt=backup_space.get_compression_algorithm().name,
            level=backup_space.get_compression_level(),
            exclude=exclude,
            verbosity_level=verbosity_level,
            overwrite=True,
        )
        moved_path = Path(shutil.move(archive_path, backup_space.get_backup_dir()))

        cls = cls(
            path=moved_path,
            backup_space=backup_space,
            unique_id=unique_id,
            sha256sum=_calculate_sha256sum(moved_path),
            comment=comment,
            created_at=created_at,
            remote=backup_space.get_remote(),
        )

        cls._config.create()
        cls.update_config()
        cls._config.prepend_no_edit_warning()

        if verbosity_level >= 1:
            print(
                f"Created Backup with UUID '{unique_id}'. "
                f"Took {timedelta(seconds=time.time() - start_time).total_seconds()}"
                " seconds!"
            )
        if verbosity_level >= 2:
            print(f"SHA256 Hash: {cls.get_hash()}")

        if cls._remote:
            cls._remote.upload(
                source=moved_path,
                target=cls.get_remote_archive_path(),
                verbosity_level=verbosity_level,
            )
            cls._remote.upload(
                source=cls._config.get_path(),
                target=cls.get_remote_config_path(),
                verbosity_level=verbosity_level,
            )

        return cls

    #####################
    #       GETTER      #
    #####################

    def get_path(self) -> Path:
        return self._path

    def get_remote_archive_path(self) -> str:
        return str(Path(self._backup_space.get_remote_path()) / self._path.name)

    def get_remote_config_path(self) -> str:
        return str(
            Path(self._backup_space.get_remote_path()) / self._config.get_path().name
        )

    def get_remote(self) -> Remote:
        return self._remote

    def get_uuid(self) -> uuid.UUID:
        return self._uuid

    def get_hash(self) -> str:
        return self._hash

    def get_comment(self) -> str:
        return self._comment

    def get_created_at(self) -> TimeObject:
        return self._created_at

    def get_config(self) -> dict:
        return self._config.as_dict()

    def get_file_size(self) -> float:
        return self._path.stat().st_size
