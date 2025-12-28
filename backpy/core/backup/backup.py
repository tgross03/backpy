from __future__ import annotations

import shutil
import time
import uuid
import warnings
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from mergedeep import merge
from rich import box
from rich.table import Table

from backpy.cli.colors import EFFECTS, RESET, get_default_palette
from backpy.core.backup import compression
from backpy.core.config import TOMLConfiguration
from backpy.core.remote import Remote
from backpy.core.utils import TimeObject, bytes2str, calculate_sha256sum
from backpy.core.utils.exceptions import InvalidBackupError, InvalidChecksumError

if TYPE_CHECKING:
    from backpy.core.space import BackupSpace

palette = get_default_palette()

__all__ = ["Backup"]


class Backup:
    def __init__(
        self,
        path: Path | None,
        backup_space: BackupSpace,
        unique_id: uuid.UUID,
        sha256sum: str,
        comment: str,
        created_at: TimeObject,
        remote: Remote | None,
        exclude: list[str] | None = None,
        include: list[str] | None = None,
        locked: bool = False,
    ):
        if exclude is None:
            exclude = []
        if include is None:
            include = []

        self._path: Path | None = path
        self._backup_space: BackupSpace = backup_space
        self._uuid: uuid.UUID = unique_id
        self._hash: str = sha256sum
        self._comment: str = comment
        self._created_at: TimeObject = created_at
        self._remote: Remote | None = remote
        self._config: TOMLConfiguration = TOMLConfiguration(
            backup_space.get_backup_dir() / (str(unique_id) + ".toml")
        )
        self._exclude: list[str] = exclude
        self._include: list[str] = include
        self._locked: bool = locked

    def calculate_hash(self) -> str:
        return calculate_sha256sum(self._path)

    def check_hash(self, remote=False, verbosity_level: int = 1) -> bool:
        if remote and self.has_remote_archive():
            if verbosity_level >= 2:
                print(
                    "Remote ->",
                    self._remote.get_hash(
                        target=self.get_remote_archive_path(),
                        verbosity_level=verbosity_level,
                    ),
                )
                print("Config ->", self._hash)
            return (
                self._remote.get_hash(
                    target=self.get_remote_archive_path(),
                    verbosity_level=verbosity_level,
                )
                == self._hash
            )

        elif self.has_local_archive():
            if verbosity_level >= 2:
                print("Local", self.calculate_hash())
                print("Config", self._hash)

            return self.calculate_hash() == self._hash
        else:
            return False

    def delete(self, verbosity_level: int = 1) -> None:
        start_time = time.time()

        self._config.get_path().unlink()
        if verbosity_level >= 2:
            print(f"Removed local config at {self._config.get_path()}.")

        if self.has_local_archive():
            self._path.unlink()
            if verbosity_level >= 2:
                print(f"Removed local backup at {self._path}.")

        if self.has_remote_archive():
            try:
                if not self._remote.is_connected():
                    with self._remote(context_verbosity=verbosity_level):
                        self._remote.remove(
                            target=self.get_remote_archive_path(),
                            verbosity_level=verbosity_level,
                        )
                        self._remote.remove(
                            target=self.get_remote_config_path(),
                            verbosity_level=verbosity_level,
                        )
                else:
                    self._remote.remove(
                        target=self.get_remote_archive_path(),
                        verbosity_level=verbosity_level,
                    )
                    self._remote.remove(
                        target=self.get_remote_config_path(),
                        verbosity_level=verbosity_level,
                    )
            except Exception:
                print(
                    f"The backup with UUID {self._uuid} could not be deleted from its remote. "
                    f"You might have to delete it manually."
                )

        if verbosity_level >= 1:
            print(
                f"Deleted backup with UUID '{self._uuid}'.\n"
                f"Took {timedelta(seconds=time.time() - start_time).total_seconds()} "
                "seconds."
            )

    def lock(self, verbosity_level: int = 1):
        self._locked = True
        self.update_config(verbosity_level=verbosity_level)

    def unlock(self, verbosity_level: int = 1):
        self._locked = False
        self.update_config(verbosity_level=verbosity_level)

    def update_config(self, verbosity_level: int = 1):
        current_content = self._config.as_dict()

        content = {
            "uuid": str(self._uuid),
            "backup_space": str(self._backup_space.get_uuid()),
            "hash": self._hash,
            "comment": self._comment,
            "created_at": self._created_at.isoformat(),
            "remote": str(self._remote.get_uuid()) if self._remote else "",
            "exclude": self._exclude,
            "include": self._include,
            "locked": self._locked,
        }

        self._config.dump_dict(dict(merge({}, current_content, content)))

        if self.has_remote_archive():
            with self._remote():
                self._remote.remove(
                    target=self.get_remote_config_path(),
                    verbosity_level=verbosity_level,
                )
                self._remote.upload(
                    source=self._config.get_path(), target=self.get_remote_config_path()
                )

    def restore(
        self, incremental: bool, source: str, force: bool, verbosity_level: int = 1
    ) -> None:
        self._backup_space.get_as_child_class().restore_backup(
            unique_id=str(self._uuid),
            incremental=incremental,
            source=source,
            force=force,
            verbosity_level=verbosity_level,
        )

    def get_info_table(
        self, check_hash: bool = False, verbosity_level: int = 1
    ) -> Table:
        table = Table(
            title=f"{palette.blue}BACKUP INFORMATION{RESET}",
            show_header=False,
            show_edge=True,
            header_style=palette.overlay1,
            box=box.HORIZONTALS,
            expand=False,
            pad_edge=False,
        )

        table.add_column(justify="right", no_wrap=False)
        table.add_column(justify="left", no_wrap=False)

        table.add_row(f"{palette.sky}UUID", f"{palette.base}{self._uuid}")
        table.add_row(
            f"{palette.sky}Backup Space",
            f"{palette.base}{self._backup_space.get_name()} "
            f"(UUID: {self._backup_space.get_uuid()})",
        )
        table.add_row(
            f"{palette.sky}Locked",
            f"{palette.red if self._locked else palette.green}{self._locked}",
        )
        table.add_row(f"{palette.sky}SHA256 Hash", f"{palette.base}{self._hash}")
        if check_hash:
            table.add_section()
            table.add_row(f"{palette.sky}Hash Check", "")  # same style as others

            if self.has_local_archive():
                local_check = (
                    f"{palette.green}passed{RESET}"
                    if self.check_hash(remote=False, verbosity_level=verbosity_level)
                    else f"{palette.maroon}failed{RESET}"
                )
                table.add_row(f"{palette.sky}> Local", f"{palette.base}{local_check}")

            if self.has_remote_archive():
                remote_check = (
                    f"{palette.green}passed{RESET}"
                    if self.check_hash(remote=True, verbosity_level=verbosity_level)
                    else f"{palette.maroon}failed{RESET}"
                )
                table.add_row(f"{palette.sky}> Remote", f"{palette.base}{remote_check}")
            table.add_section()
        table.add_row(
            f"{palette.sky}Comment",
            f"{palette.base}{self._comment or f'{EFFECTS.dim.on}N/A{EFFECTS.dim.off}'}",
        )
        table.add_row(
            f"{palette.sky}File size",
            f"{palette.base}{bytes2str(self.get_file_size(verbosity_level=verbosity_level))}",
        )
        table.add_row(
            f"{palette.sky}Created At",
            f"{palette.base}{self._created_at.printformat()}",
        )

        table.add_row(
            f"{palette.sky}Excluded",
            f"{palette.base}{self._exclude}",
        )

        table.add_row(
            f"{palette.sky}Included",
            f"{palette.base}{self._include}",
        )

        remote = (
            self._remote.get_uuid()
            if self.has_remote_archive()
            else "Local backup (no remote)"
        )

        table.add_row(
            f"{palette.sky}Remote",
            f"{palette.base}{remote}",
        )

        return table

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_uuid(
        cls,
        backup_space: BackupSpace,
        unique_id: str,
        check_hash: bool = True,
        fail_invalid: bool = False,
        verbosity_level: int = 1,
    ):
        unique_id = uuid.UUID(unique_id)

        config_path = backup_space.get_backup_dir() / (str(unique_id) + ".toml")

        if not config_path.exists():
            raise InvalidBackupError(
                f"The Backup with UUID '{unique_id}' does not exist."
            )

        config = TOMLConfiguration(config_path, none_if_unknown_key=True)

        if not config.is_valid():
            raise InvalidBackupError(
                f"The Backup with UUID '{unique_id}' could not be loaded because its"
                "'config.toml' is invalid!"
            )

        archive_path = backup_space.get_backup_dir() / (
            str(unique_id) + backup_space.get_compression_algorithm().extension
        )

        try:
            remote = (
                Remote.load_by_uuid(config["remote"])
                if config["remote"] != ""
                else None
            )
        except Exception:
            remote = None

        cls = cls(
            path=archive_path if archive_path.exists() else None,
            backup_space=backup_space,
            unique_id=unique_id,
            sha256sum=config["hash"],
            comment=config["comment"],
            created_at=TimeObject.fromisoformat(config["created_at"]),
            remote=(
                remote
                if remote is None
                or (
                    remote is not None
                    and remote.get_uuid() != backup_space.get_remote().get_uuid()
                )
                else backup_space.get_remote()
            ),
            exclude=config["exclude"],
            include=config["include"],
            locked=config["locked"] if config["locked"] is not None else False,
        )

        if check_hash:
            checks = []

            if not cls.has_remote_archive() and not cls.has_local_archive():
                raise InvalidBackupError(
                    "The backup exists but does not have any local or remote archives."
                )

            if cls.has_remote_archive():
                checks.append(True)
            if cls.has_local_archive():
                checks.append(False)

            for remote in checks:
                if not cls.check_hash(remote=remote, verbosity_level=verbosity_level):
                    err_msg = (
                        f"The SHA256 of the loaded backup with UUID '{unique_id}' "
                        "is not identical with the one saved in its configuration. "
                        "This could mean, that the file is corrupted or was changed. "
                        f"(Location: {'remote' if remote else 'local'})"
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
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        lock: bool = False,
        location: str = "all",
        verbosity_level: int = 1,
    ):
        save_locally = location == "local" or location == "all"
        save_remotely = location == "remote" or location == "all"

        if not source_path.exists(follow_symlinks=True):
            raise FileNotFoundError(
                "The given source path could not be found at path "
                f"'{source_path.absolute()}'!"
            )

        start_time = time.time()

        if exclude is None:
            exclude = []

        if include is None:
            include = []

        unique_id = uuid.uuid4()
        created_at = TimeObject.localnow()

        if verbosity_level >= 1:
            print(f"Creating Backup with UUID '{unique_id}'...")

        archive_path = compression.compress(
            root_path=source_path,
            archive_name=str(unique_id),
            fmt=backup_space.get_compression_algorithm().name,
            level=backup_space.get_compression_level(),
            include=include,
            exclude=exclude,
            verbosity_level=verbosity_level,
            overwrite=True,
        )
        moved_path = Path(shutil.move(archive_path, backup_space.get_backup_dir()))

        cls = cls(
            path=moved_path if save_locally else None,
            backup_space=backup_space,
            unique_id=unique_id,
            sha256sum=calculate_sha256sum(moved_path),
            comment=comment,
            created_at=created_at,
            remote=backup_space.get_remote() if save_remotely else None,
            exclude=exclude,
            include=include,
            locked=lock,
        )

        cls._config.create()
        cls.update_config()
        cls._config.prepend_no_edit_warning()

        if cls._backup_space.is_backup_limit_reached(post_creation=True):
            if cls._backup_space.is_auto_deletion_active():
                cls._backup_space.perform_auto_deletion(verbosity_level=verbosity_level)
            else:
                moved_path.unlink(missing_ok=True)
                cls._config.get_path().unlink(missing_ok=True)
                raise MemoryError(
                    f"The backup space has reached its maximum number of backups: "
                    f"{len(cls._backup_space.get_backups())} / "
                    f"{cls._backup_space.get_max_backups()}."
                )

        if cls._backup_space.is_disk_limit_reached(verbosity_level=verbosity_level):
            error_msg = (
                f"The backup space has reached its maximum disk usage: "
                f"{bytes2str(cls._backup_space.get_disk_usage(verbosity_level=verbosity_level))} / "
                f"{bytes2str(cls._backup_space.get_max_size())}. "
                f"Delete a backup or raise the limit."
            )
            moved_path.unlink(missing_ok=True)
            cls._config.get_path().unlink(missing_ok=True)
            raise MemoryError(error_msg)

        if verbosity_level >= 1:
            print(
                f"Created Backup with UUID '{unique_id}'. "
                f"Took {timedelta(seconds=time.time() - start_time).total_seconds()}"
                " seconds!"
            )

        if verbosity_level >= 2:
            print(f"SHA256 Hash: {cls.get_hash()}")

        if cls.get_remote() is not None:
            with cls._remote(context_verbosity=verbosity_level):
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

        if not save_locally:
            if cls.get_remote() is not None:
                moved_path.unlink()
                if verbosity_level >= 2:
                    print(f"Removed local backup at {moved_path}.")
            else:
                warnings.warn(
                    "Since there is no remote defined, the backup can only be saved locally!"
                )

        return cls

    #####################
    #       GETTER      #
    #####################

    def has_local_archive(self) -> bool:
        return self._path is not None and self._path.exists()

    def has_remote_archive(self) -> bool:
        return self._remote is not None and self._remote.exists(
            target=self.get_remote_archive_path()
        )

    def get_path(self) -> Path | None:
        return self._path

    def get_remote_archive_path(self) -> str:
        return str(
            Path(self._backup_space.get_remote_path())
            / (
                str(self._uuid)
                + self._backup_space.get_compression_algorithm().extension
            )
        )

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

    def get_file_size(self, verbosity_level: int = 1) -> int:
        if self.has_local_archive():
            return int(self._path.stat().st_size)
        elif self.has_remote_archive():
            return int(
                self._remote.get_file_size(
                    target=self.get_remote_archive_path(),
                    verbosity_level=verbosity_level,
                )
            )
        else:
            raise FileNotFoundError("This backup does not have a valid archive!")

    def get_exclude(self) -> list[str]:
        return self._exclude

    def get_include(self) -> list[str]:
        return self._include

    def is_locked(self) -> bool:
        return self._locked

    def is_full_backup(self) -> bool:
        return (
            len(self._exclude) == 0
            and len(self._include) == 0
            or len(self._exclude) == 0
            and "*" in self._include
        )
