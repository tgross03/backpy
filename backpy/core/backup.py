import shutil
import time
import uuid
import warnings
from dataclasses import dataclass
from datetime import timedelta
from hashlib import file_digest
from pathlib import Path

import numpy as np

from backpy import TimeObject, TOMLConfiguration, VariableLibrary, compression


@dataclass
class BackupSpaceType:
    name: str
    description: str

    @classmethod
    def from_name(cls, name):
        for backup_space_type in _backup_space_types:
            if backup_space_type.name == name:
                return backup_space_type
        return None


_backup_space_types = [
    BackupSpaceType(
        "SQL_DATABASE", "Backup-Space of an SQL-based database and its tables."
    ),
    BackupSpaceType(
        "FILE_SYSTEM", "Backup-Space of one or more files and/or directories."
    ),
]


def _calculate_sha256sum(path: Path) -> str:
    with open(path, "rb") as f:
        digest = file_digest(f, "sha256")
    return digest.hexdigest()


class BackupSpace:
    def __init__(
        self,
        name: str,
        unique_id: uuid.UUID,
        space_type: BackupSpaceType,
        compression_algorithm: compression.CompressionAlgorithm,
        compression_level: int,
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
            path=self._backup_dir / "config.toml"
        )

    def create_backup(self, comment: str = "", verbosity_level: int = 1) -> None:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def restore_backup(
        self, unique_id: str, incremental: bool, force: bool = False
    ) -> None:
        raise NotImplementedError("This method is abstract and has to be overridden!")

    def get_backups(self, sort_by: str | None = None) -> list["Backup"]:
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
            except FileNotFoundError:
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

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_uuid(cls, unique_id: str):

        unique_id = uuid.UUID(unique_id)

        path = Path(VariableLibrary().get_variable("paths.backup_directory")) / str(
            unique_id
        )

        if not path.is_dir():
            raise NotADirectoryError(
                f"There is no BackupSpace present with the UUID '{unique_id}'."
            )

        config = TOMLConfiguration(path=path / "config.toml")

        if not config.is_valid():
            raise FileNotFoundError(
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
            except NotADirectoryError:
                break

        raise FileNotFoundError(
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
    ):
        if not compression.is_algorithm_available(compression_algorithm):
            raise KeyError(
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
        )
        cls._backup_dir.mkdir(exist_ok=True, parents=True)
        cls._config.dump_dict(
            {
                "general": {
                    "name": cls._name,
                    "uuid": str(cls._uuid),
                    "type": cls._type.name,
                    "compression_algorithm": cls._compression_algorithm.name,
                    "compression_level": cls._compression_level,
                }
            }
        )
        cls._config.prepend_comments(
            [
                "======================================"
                "======================================",
                "   WARNING! DO NOT EDIT THIS FILE MANUALLY! "
                "THIS COULD BREAK YOUR BACKPY!",
                "======================================"
                "======================================",
            ]
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


class Backup:
    def __init__(
        self,
        path: Path,
        backup_space: BackupSpace,
        unique_id: uuid.UUID,
        sha256sum: str,
        comment: str,
        created_at: TimeObject,
    ):
        self._path: Path = path
        self._backup_space: BackupSpace = backup_space
        self._uuid: uuid.UUID = unique_id
        self._hash: str = sha256sum
        self._comment: str = comment
        self._created_at: TimeObject = created_at
        self._config: TOMLConfiguration = TOMLConfiguration(
            path.parent / (str(unique_id) + ".toml")
        )

    def calculate_hash(self) -> str:
        return _calculate_sha256sum(self._path)

    def check_hash(self) -> bool:
        return self.calculate_hash() == self._hash

    def delete(self) -> None:
        self._config.get_path().unlink()
        self._path.unlink()

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
            raise FileNotFoundError(
                f"The Backup with UUID '{unique_id}' does not exist."
            )

        config = TOMLConfiguration(
            backup_space.get_backup_dir() / (str(unique_id) + ".toml")
        )

        if not config.is_valid():
            raise FileNotFoundError(
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
        )

        if not cls.check_hash():
            err_msg = (
                f"The SHA256 of the loaded backup with UUID '{unique_id}' "
                "is not identical with the one saved in its configuration. "
                "This could mean, that the file is corrupted or was changed."
            )
            if not fail_invalid:
                warnings.warn("IMPORTANT! " + err_msg)
            else:
                raise ValueError(err_msg)

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
        )

        cls._config.create()
        cls._config.dump_dict(
            {
                "uuid": str(cls._uuid),
                "backup_space": str(cls._backup_space.get_uuid()),
                "hash": cls._hash,
                "comment": cls._comment,
                "created_at": cls._created_at.isoformat(),
            }
        )
        cls._config.prepend_comments(
            [
                "======================================"
                "======================================",
                "   WARNING! DO NOT EDIT THIS FILE MANUALLY! "
                "THIS COULD BREAK YOUR BACKPY!",
                "======================================"
                "======================================",
            ]
        )

        if verbosity_level >= 1:
            print(
                f"Created Backup with UUID '{unique_id}'. "
                f"Took {timedelta(seconds=time.time() - start_time).total_seconds()}"
                " seconds!"
            )
        if verbosity_level >= 2:
            print(f"SHA256 Hash: {cls.get_hash()}")

        return cls

    #####################
    #       GETTER      #
    #####################

    def get_path(self) -> Path:
        return self._path

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
