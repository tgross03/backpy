from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from mergedeep import merge
from rich import box
from rich.table import Table

from backpy.cli.colors import RESET, get_default_palette
from backpy.core.backup import compression
from backpy.core.config import TOMLConfiguration, VariableLibrary
from backpy.core.remote import Remote
from backpy.core.utils.exceptions import (
    InvalidBackupError,
    InvalidBackupSpaceError,
    UnsupportedCompressionAlgorithmError, InvalidRemoteError,
)

if TYPE_CHECKING:
    from backpy import Backup, BackupSpaceType

palette = get_default_palette()


class BackupSpace:
    def __init__(
        self,
        name: str,
        unique_id: uuid.UUID,
        space_type: BackupSpaceType,
        compression_algorithm: compression.CompressionAlgorithm,
        compression_level: int,
        default_include: list[str],
        default_exclude: list[str],
        remote: Remote | None,
    ):
        self._uuid: uuid.UUID = unique_id
        self._name: str = name
        self._type: BackupSpaceType = space_type
        self._compression_algorithm: compression.CompressionAlgorithm = compression_algorithm
        self._compression_level: int = compression_level
        self._backup_dir: Path = Path(
            VariableLibrary().get_variable("paths.backup_directory")
        ) / str(self._uuid)
        self._config: TOMLConfiguration = TOMLConfiguration(
            path=self._backup_dir / "config.toml",
        )
        self._default_include: list[str] = default_include
        self._default_exclude: list[str] = default_exclude
        self._remote: Remote | None = remote

    def create_backup(
        self,
        comment: str = "",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        location: str = "all",
        verbosity_level: int = 1,
    ) -> None:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def restore_backup(
        self,
        unique_id: str,
        incremental: bool,
        source: str = "local",
        force: bool = False,
        verbosity_level: int = 1,
    ) -> None:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def get_backups(self, sort_by: str | None = None, check_hash: bool = True) -> list[Backup]:

        from backpy import Backup

        archive_files = [
            file if file.is_file() else None
            for file in self._backup_dir.glob(f"*{self._compression_algorithm.extension}")
        ]

        backups = []

        for archive_file in archive_files:
            try:
                backups.append(Backup.load_by_uuid(self, archive_file.stem, check_hash=check_hash))
            except InvalidBackupError:
                continue

        if sort_by is not None:
            match sort_by:
                case "date":
                    backups.sort(key=lambda b: b.get_created_at().get_datetime(), reverse=True)
                case "size":
                    backups.sort(key=lambda b: b.get_file_size(), reverse=True)

        return backups

    def update_config(self):
        current_content = self._config.as_dict()

        content = {
            "general": {
                "name": self._name,
                "type": self._type.name,
                "uuid": str(self._uuid),
                "remote": str(self._remote.get_uuid()) if self._remote else "",
                "compression_algorithm": self._compression_algorithm.name,
                "compression_level": self._compression_level,
                "default_include": self._default_include,
                "default_exclude": self._default_exclude,
            }
        }

        self._config.dump_dict(dict(merge({}, current_content, content)))

    def delete(self, verbosity_level: int = 1):
        shutil.rmtree(self._backup_dir)
        if verbosity_level > 1:
            print(f"Removing backup directory {self._backup_dir}")

        if self._remote is not None:
            with self._remote(context_verbosity=verbosity_level):
                self._remote.remove(target=self.get_remote_path(), verbosity_level=verbosity_level)
        if verbosity_level > 1:
            print(
                f"Removing remote backup directory from remote {self._remote.get_name()} "
                f"(UUID: {self._remote.get_uuid()}) at {self.get_remote_path()}."
            )

    def get_info_table(self) -> Table:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def _get_info_table(self, additional_info_idx: list[int], additional_info: dict) -> Table:
        info = {
            "Name": self._name,
            "UUID": self._uuid,
            "Type": self._type.full_name,
            "Remote": (
                f"{self._remote.get_name()} " f"(UUID: {self._remote.get_uuid()})"
                if self._remote is not None
                else "none"
            ),
            "Compression Algorithm": self._compression_algorithm.name,
            "Compression Level": self._compression_level,
            "Include": self._default_include,
            "Exclude": self._default_exclude,
        }
        keys, values = list(info.keys()), list(info.values())
        additional_keys, additional_values = (
            list(additional_info.keys()),
            list(additional_info.values()),
        )

        for idx, i in zip(additional_info_idx, range(len(additional_info))):
            keys.insert(idx, additional_keys[i])
            values.insert(idx, additional_values[i])

        table = Table(
            title=f"{palette.peach}BACKUP SPACE INFORMATION{RESET}",
            show_header=False,
            show_edge=True,
            header_style=palette.overlay1,
            box=box.HORIZONTALS,
            expand=False,
            pad_edge=False,
        )

        for key, value in zip(keys, values):
            table.add_row(f"{palette.sky}{key}{RESET}", f"{palette.base}{value}{RESET}")

        return table

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def get_backup_spaces(cls) -> list[BackupSpace]:
        spaces = []
        for directory in Path(VariableLibrary().get_variable("paths.backup_directory")).glob("*"):
            tomlf = directory / "config.toml"
            if directory.is_dir() and TOMLConfiguration(tomlf).is_valid():
                spaces.append(BackupSpace.load_by_uuid(directory.name))

        return spaces

    @classmethod
    def load_by_uuid(cls, unique_id: str):

        from .types import BackupSpaceType

        unique_id = uuid.UUID(unique_id)

        path = Path(VariableLibrary().get_variable("paths.backup_directory")) / str(unique_id)

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

        remote = None
        try:
            remote = Remote.load_by_uuid(config["general.remote"])
        except InvalidRemoteError:
            pass

        cls = cls(
            name=config["general.name"],
            unique_id=unique_id,
            space_type=BackupSpaceType.from_name(config["general.type"]),
            compression_algorithm=compression.CompressionAlgorithm.from_name(
                config["general.compression_algorithm"]
            ),
            compression_level=config["general.compression_level"],
            default_include=config["general.default_include"],
            default_exclude=config["general.default_exclude"],
            remote=,
        )
        return cls

    @classmethod
    def load_by_name(cls, name: str):
        for tomlf in Path(VariableLibrary().get_variable("paths.backup_directory")).rglob(
            "config.toml"
        ):
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
        default_include: list[str] | None = None,
        default_exclude: list[str] | None = None,
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
            compression_algorithm=compression.CompressionAlgorithm.from_name(compression_algorithm),
            compression_level=compression_level,
            default_include=default_include if default_include is not None else [],
            default_exclude=default_exclude if default_exclude is not None else [],
            remote=remote,
        )
        cls._backup_dir.mkdir(exist_ok=True, parents=True)

        cls._config.create()
        cls.update_config()
        cls._config.prepend_no_edit_warning()

        if cls._remote:
            with cls._remote(context_verbosity=verbosity_level):
                cls._remote.mkdir(
                    target=cls.get_remote_path(),
                    parents=True,
                    verbosity_level=verbosity_level,
                )

        if verbosity_level >= 1:
            print(f"Created BackupSpace '{name}' (UUID: {cls._uuid})!")

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

    def get_default_include(self) -> list[str]:
        return self._default_include

    def get_default_exclude(self) -> list[str]:
        return self._default_exclude

    def get_backup_dir(self) -> Path:
        return self._backup_dir

    def get_config(self) -> dict:
        return self._config.as_dict()

    def get_disk_usage(self) -> int:
        return np.sum([backup.get_file_size() for backup in self.get_backups(check_hash=False)])
