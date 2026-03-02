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
from backpy.core.backup.backup import RestoreMode
from backpy.core.backup.scheduling import Schedule
from backpy.core.config import TOMLConfiguration, VariableLibrary
from backpy.core.config.configuration import MissingKeyPolicy
from backpy.core.remote import Remote
from backpy.core.utils import bytes2str
from backpy.core.utils.exceptions import (
    InvalidBackupSpaceError,
    UnsupportedCompressionAlgorithmError,
)

if TYPE_CHECKING:
    from backpy.core.backup import Backup
    from backpy.core.space import BackupSpaceType

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
        max_backups: int = -1,
        max_size: int = -1,
        auto_deletion: bool = False,
        auto_deletion_rule: str = "oldest",
    ):
        self._uuid: uuid.UUID = unique_id
        self._name: str = name
        self._type: BackupSpaceType = space_type
        self._compression_algorithm: compression.CompressionAlgorithm = (
            compression_algorithm
        )
        self._compression_level: int = compression_level
        self._backup_dir: Path = Path(
            VariableLibrary.get_variable("paths.backup_directory")
        ) / str(self._uuid)
        self._config: TOMLConfiguration = TOMLConfiguration(
            path=self._backup_dir / "config.toml",
        )
        self._default_include: list[str] = default_include
        self._default_exclude: list[str] = default_exclude

        self._max_backups: int = max_backups if max_backups is not None else -1
        self._max_size: int = max_size if max_size is not None else -1

        self._auto_deletion: bool = (
            auto_deletion if auto_deletion is not None else False
        )
        self._auto_deletion_rule: str = (
            auto_deletion_rule if auto_deletion_rule is not None else "oldest"
        )

        self._remote: Remote | None = remote

    def create_backup(
        self,
        comment: str = "",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        lock: bool = False,
        location: str = "all",
        verbosity_level: int = 1,
    ) -> None:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def restore_backup(
        self,
        unique_id: str,
        mode: RestoreMode,
        source: str = "local",
        force: bool = False,
        verbosity_level: int = 1,
    ) -> None:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def get_backups(
        self,
        sort_by: str | None = None,
        check_hash: bool = True,
        unlocked_only: bool = False,
        verbosity_level: int = 1,
    ) -> list[Backup]:

        from backpy.core.backup import Backup

        configurations = [
            file if file.is_file() else None for file in self._backup_dir.glob("*.toml")
        ]

        backups = []

        for config in configurations:
            try:
                backup = Backup.load_by_uuid(
                    backup_space=self, unique_id=config.stem, check_hash=check_hash
                )
                if backup.is_locked() and unlocked_only:
                    continue
                backups.append(backup)
            except Exception:
                pass

        if sort_by is not None:
            match sort_by:
                case "date":
                    backups.sort(
                        key=lambda b: b.get_created_at().get_datetime(), reverse=True
                    )
                case "size":
                    backups.sort(
                        key=lambda b: b.get_file_size(verbosity_level=verbosity_level),
                        reverse=True,
                    )

        return backups

    def update_config(self) -> None:
        current_content = self._config.asdict()

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
            },
            "limits": {
                "max_backups": self._max_backups,
                "max_size": self._max_size,
                "auto_deletion": self._auto_deletion,
                "auto_deletion_rule": self._auto_deletion_rule,
            },
        }

        self._config.dump(dict(merge({}, current_content, content)))

    def clear(self, verbosity_level: int = 1) -> None:
        if self._remote is not None:
            with self._remote(context_verbosity=verbosity_level):
                for backup in self.get_backups(check_hash=False):
                    backup.delete(verbosity_level=verbosity_level)
        else:
            for backup in self.get_backups(check_hash=False):
                backup.delete(verbosity_level=verbosity_level)

        if verbosity_level > 1:
            print(
                f"Deleted all backups from backup space {self._name} (UUID: {self._uuid})"
            )

    def delete(self, verbosity_level: int = 1) -> None:
        shutil.rmtree(self._backup_dir)

        schedules = Schedule.load_by_backup_space(backup_space=self)
        for schedule in schedules:
            schedule.delete(verbosity_level=verbosity_level)

        if verbosity_level > 1:
            print(f"Removing backup directory {self._backup_dir}")

        if self._remote is not None:
            with self._remote(context_verbosity=verbosity_level):
                try:
                    self._remote.remove(
                        target=self.get_remote_path(), verbosity_level=verbosity_level
                    )
                except FileNotFoundError:
                    pass

            if verbosity_level > 1:
                print(
                    f"Removing remote backup directory from remote {self._remote.get_name()} "
                    f"(UUID: {self._remote.get_uuid()}) at {self.get_remote_path()}."
                )

        if verbosity_level >= 1:
            print(f"Deleted backup space (UUID: {self._uuid})")

    def perform_auto_deletion(self, verbosity_level: int = 1) -> None:

        if verbosity_level >= 1:
            print(
                f"Performing automatic deletion of '{self._auto_deletion_rule}' backup."
            )

        while len(self.get_backups()) > 0 and (
            self.is_backup_limit_reached()
            or self.is_disk_limit_reached(verbosity_level=verbosity_level)
        ):
            match self._auto_deletion_rule:
                case "oldest":
                    backup = self.get_backups(sort_by="date", check_hash=False)[-1]
                case "newest":
                    backup = self.get_backups(sort_by="date", check_hash=False)[0]
                case "largest":
                    backup = self.get_backups(sort_by="size", check_hash=False)[0]
                case "smallest":
                    backup = self.get_backups(sort_by="size", check_hash=False)[-1]
            backup.delete(verbosity_level=verbosity_level)

    def get_info_table(self, verbosity_level: int = 1) -> Table:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def _get_info_table(
        self,
        additional_info_idx: list[int],
        additional_info: dict,
        verbosity_level: int = 1,
    ) -> Table:
        info = {
            "Name": self._name,
            "UUID": self._uuid,
            "Type": self._type.full_name,
            "Backups": f"{len(self.get_backups())} / "
            f"{'∞' if self._max_backups == -1 else self._max_backups}",
        }

        if self._remote is not None:
            info = info | {
                "Disk Usage": f"{bytes2str(self.get_disk_usage(verbosity_level=verbosity_level))} "
                f"/ {bytes2str(self._max_size)}"
            }
        else:
            info = info | {
                "Disk Usage": f"{bytes2str(self.get_disk_usage(verbosity_level=verbosity_level))} "
                f"/ {bytes2str(self._max_size)}"
            }

        info = info | {
            "Remote": (
                f"{self._remote.get_name()} " f"(UUID: {self._remote.get_uuid()})"
                if self._remote is not None
                else "none"
            ),
            "Compression Algorithm": self._compression_algorithm.name,
            "Compression Level": self._compression_level,
            "Include": self._default_include,
            "Exclude": self._default_exclude,
            "Automatic Deletion active?": self._auto_deletion,
        }

        if self._auto_deletion:
            info = info | {
                "Automatic Deletion rule": self._auto_deletion_rule,
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

    def get_as_child_class(self) -> "BackupSpace":
        return self.get_type().child_class.load_by_uuid(unique_id=str(self._uuid))

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def get_backup_spaces(cls) -> list["BackupSpace"]:
        spaces = []
        for directory in Path(
            VariableLibrary.get_variable("paths.backup_directory")
        ).glob("*"):
            tomlf = directory / "config.toml"
            if directory.is_dir() and TOMLConfiguration(tomlf).exists():
                spaces.append(BackupSpace.load_by_uuid(directory.name))

        return spaces

    @classmethod
    def load_by_uuid(cls, unique_id: str) -> "BackupSpace":

        from .types import BackupSpaceType

        unique_id = uuid.UUID(unique_id)

        path = Path(VariableLibrary.get_variable("paths.backup_directory")) / str(
            unique_id
        )

        if not path.is_dir():
            raise InvalidBackupSpaceError(
                f"There is no BackupSpace present with the UUID '{unique_id}'."
            )

        config = TOMLConfiguration(
            path=path / "config.toml", missing_key_policy=MissingKeyPolicy.RETURN_NONE
        )

        if not config.exists():
            raise InvalidBackupSpaceError(
                "The BackupSpace could not be loaded because its"
                "'config.toml' is invalid or missing!"
            )

        remote = None
        try:
            remote = Remote.load_by_uuid(config["general.remote"])
        except Exception:
            pass

        cls = cls(
            name=config["general.name"],
            unique_id=unique_id,
            space_type=BackupSpaceType[config["general.type"]],
            compression_algorithm=compression.CompressionAlgorithm.from_name(
                config["general.compression_algorithm"]
            ),
            compression_level=config["general.compression_level"],
            default_include=config["general.default_include"],
            default_exclude=config["general.default_exclude"],
            max_backups=config["limits.max_backups"],
            max_size=config["limits.max_size"],
            auto_deletion=config["limits.auto_deletion"],
            auto_deletion_rule=config["limits.auto_deletion_rule"],
            remote=remote,
        )
        return cls

    @classmethod
    def load_by_name(cls, name: str) -> "BackupSpace":
        for tomlf in Path(VariableLibrary.get_variable("paths.backup_directory")).rglob(
            "config.toml"
        ):
            config = TOMLConfiguration(tomlf, create_if_not_exists=False)

            if not config.exists():
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
        compression_algorithm: str = VariableLibrary.get_variable(
            "backup.states.default_compression_algorithm"
        ),
        compression_level: int = VariableLibrary.get_variable(
            "backup.states.default_compression_level"
        ),
        default_include: list[str] | None = None,
        default_exclude: list[str] | None = None,
        max_backups: int = -1,
        max_size: int = -1,
        auto_deletion: bool = False,
        auto_deletion_rule: str = False,
        remote: Remote = None,
        verbosity_level: int = 1,
    ) -> "BackupSpace":
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
            default_include=default_include if default_include is not None else [],
            default_exclude=default_exclude if default_exclude is not None else [],
            max_backups=max_backups,
            max_size=max_size,
            auto_deletion=auto_deletion,
            auto_deletion_rule=auto_deletion_rule,
            remote=remote,
        )
        cls._backup_dir.mkdir(exist_ok=True, parents=True)

        cls._config.create()
        cls.update_config()

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

    def get_remote_path(self) -> str | None:
        if self._remote is not None:
            return self._remote.get_relative_to_root(path=f"backups/{self._uuid}")
        else:
            return None

    def get_compression_algorithm(self) -> compression.CompressionAlgorithm:
        return self._compression_algorithm

    def get_compression_level(self) -> int:
        return self._compression_level

    def get_default_include(self) -> list[str]:
        return self._default_include

    def get_default_exclude(self) -> list[str]:
        return self._default_exclude

    def is_backup_limit_reached(self, post_creation: bool = False) -> bool:
        if self._max_backups == -1:
            return False

        offset = 0 if not post_creation else 1
        return len(self.get_backups()) - offset >= self._max_backups

    def is_disk_limit_reached(self, verbosity_level: int = 1) -> bool:
        if self._max_size == -1:
            return False

        return self.get_disk_usage(verbosity_level=verbosity_level) >= self._max_size

    def get_max_backups(self) -> int:
        return self._max_backups

    def get_max_size(self) -> int:
        return self._max_size

    def is_auto_deletion_active(self) -> bool:
        return self._auto_deletion

    def get_auto_deletion_rule(self) -> str:
        return self._auto_deletion_rule

    def get_backup_dir(self) -> Path:
        return self._backup_dir

    def get_config(self) -> dict:
        return self._config.asdict()

    def get_disk_usage(self, verbosity_level: int = 1) -> int:
        if self._remote is not None:
            with self._remote(context_verbosity=verbosity_level):
                size = np.sum(
                    [
                        backup.get_file_size(verbosity_level=verbosity_level)
                        for backup in self.get_backups(check_hash=False)
                    ]
                )
        else:
            size = np.sum(
                [
                    backup.get_file_size(verbosity_level=verbosity_level)
                    for backup in self.get_backups(check_hash=False)
                ]
            )
        return np.max([0, size])
