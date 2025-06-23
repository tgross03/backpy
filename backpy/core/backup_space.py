from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from mergedeep import merge

from backpy import Remote, TOMLConfiguration, VariableLibrary
from backpy.core import compression
from backpy.exceptions import (
    InvalidBackupError,
    InvalidBackupSpaceError,
    UnsupportedCompressionAlgorithmError,
)

if TYPE_CHECKING:
    from backpy import Backup, BackupSpaceType


class BackupSpace:
    def __init__(
        self,
        name: str,
        unique_id: uuid.UUID,
        space_type: BackupSpaceType,
        compression_algorithm: compression.CompressionAlgorithm,
        compression_level: int,
        remote: Remote | None,
    ):
        self._uuid: uuid.UUID = unique_id
        self._name: str = name
        self._type: BackupSpaceType = space_type
        self._compression_algorithm: compression.CompressionAlgorithm = (
            compression_algorithm
        )
        self._compression_level: int = compression_level
        self._backup_dir: Path = Path(
            VariableLibrary().get_variable("paths.backup_directory")
        ) / str(self._uuid)
        self._config: TOMLConfiguration = TOMLConfiguration(
            path=self._backup_dir / "config.toml",
        )
        self._remote = remote

    def create_backup(self, comment: str = "", verbosity_level: int = 1) -> None:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def restore_backup(
        self,
        unique_id: str,
        incremental: bool,
        source: str = "local",
        force: bool = False,
    ) -> None:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def get_backups(self, sort_by: str | None = None) -> list[Backup]:
        archive_files = [
            file if file.is_file() else None
            for file in self._backup_dir.glob(
                f"*{self._compression_algorithm.extension}"
            )
        ]

        backups = []

        for archive_file in archive_files:
            try:
                backups.append(Backup.load_by_uuid(self, archive_file.stem))
            except InvalidBackupError:
                continue

        if sort_by is not None:
            match sort_by:
                case "date":
                    backups.sort(
                        key=lambda b: b.get_created_at().get_datetime(), reverse=True
                    )
                case "size":
                    backups.sort(key=lambda b: b.get_file_size(), reverse=True)

        return backups

    def update_config(self):
        current_content = self._config.as_dict()

        content = {
            "general": {
                "name": self._name,
                "uuid": str(self._uuid),
                "remote": str(self._remote.get_uuid()) if self._remote else "",
                "type": self._type.name,
                "compression_algorithm": self._compression_algorithm.name,
                "compression_level": self._compression_level,
            }
        }

        self._config.dump_dict(dict(merge({}, content, current_content)))

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def get_backup_spaces(cls) -> list[BackupSpace]:
        spaces = []
        for directory in Path(
            VariableLibrary().get_variable("paths.backup_directory")
        ).glob("*"):
            tomlf = directory / "config.toml"
            if directory.is_dir() and TOMLConfiguration(tomlf).is_valid():
                spaces.append(BackupSpace.load_by_uuid(directory.name))

        return spaces

    @classmethod
    def load_by_uuid(cls, unique_id: str):

        from .types import BackupSpaceType

        unique_id = uuid.UUID(unique_id)

        path = Path(VariableLibrary().get_variable("paths.backup_directory")) / str(
            unique_id
        )

        if not path.is_dir():
            raise InvalidBackupSpaceError(
                f"There is no BackupSpace present with the UUID '{unique_id}'."
            )

        config = TOMLConfiguration(path=path / "config.toml")

        if not config.is_valid():
            raise InvalidBackupSpaceError(
                "The BackupSpace could not be loaded because its"
                "'config.toml' is invalid or missing!"
            )

        cls = cls(
            name=config["general.name"],
            unique_id=unique_id,
            space_type=BackupSpaceType.from_name(config["general.type"]),
            compression_algorithm=compression.CompressionAlgorithm.from_name(
                config["general.compression_algorithm"]
            ),
            compression_level=config["general.compression_level"],
            remote=Remote.load_by_uuid(config["general.remote"])
            if config["general.remote"] != ""
            else None,
        )
        return cls

    @classmethod
    def load_by_name(cls, name: str):
        for tomlf in Path(
            VariableLibrary().get_variable("paths.backup_directory")
        ).rglob("config.toml"):
            config = TOMLConfiguration(tomlf, create_if_not_exists=False)

            if not config.is_valid():
                continue

            if name != config["general.name"]:
                continue

            try:
                return BackupSpace.load_by_uuid(config["general.uuid"])
            except InvalidBackupSpaceError:
                break

        raise InvalidBackupSpaceError(
            f"There is no valid BackupSpace present with the name '{name}'."
        )

    @classmethod
    def new(
        cls,
        name: str,
        space_type: BackupSpaceType,
        compression_algorithm: str = VariableLibrary().get_variable(
            "backup.states.default_compression_algorithm"
        ),
        compression_level: int = VariableLibrary().get_variable(
            "backup.states.default_compression_level"
        ),
        remote: Remote = None,
        verbosity_level: int = 1,
    ):
        if not compression.is_algorithm_available(compression_algorithm):
            raise UnsupportedCompressionAlgorithmError(
                f"The compression algorithm '{compression_algorithm}' is not available!"
            )

        cls = cls(
            name=name,
            unique_id=uuid.uuid4(),
            space_type=space_type,
            compression_algorithm=compression.CompressionAlgorithm.from_name(
                compression_algorithm
            ),
            compression_level=compression_level,
            remote=remote,
        )
        cls._backup_dir.mkdir(exist_ok=True, parents=True)

        cls._config.create()
        cls.update_config()
        cls._config.prepend_no_edit_warning()

        if cls._remote:
            cls._remote.mkdir(
                target=cls.get_remote_path(),
                parents=True,
                verbosity_level=verbosity_level,
            )

        return cls

    #####################
    #       GETTER      #
    #####################

    def get_uuid(self) -> uuid.UUID:
        return self._uuid

    def get_name(self) -> str:
        return self._name

    def get_type(self) -> BackupSpaceType:
        return self._type

    def get_remote(self) -> Remote:
        return self._remote

    def get_remote_path(self) -> str:
        return self._remote.get_relative_to_root("backups/" + str(self._uuid))

    def get_compression_algorithm(self) -> compression.CompressionAlgorithm:
        return self._compression_algorithm

    def get_compression_level(self) -> int:
        return self._compression_level

    def get_backup_dir(self) -> Path:
        return self._backup_dir

    def get_config(self) -> dict:
        return self._config.as_dict()

    def get_disk_usage(self) -> int:
        return np.sum([backup.get_file_size() for backup in self.get_backups()])
