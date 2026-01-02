from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import crontab
from mergedeep import merge
from rich import box
from rich.table import Table

from backpy import TOMLConfiguration, VariableLibrary
from backpy.cli.colors import RESET, get_default_palette
from backpy.core.utils.exceptions import InvalidScheduleError

COMMENT_SUFFIX = "(MANAGED BY BACKPY)"

if TYPE_CHECKING:
    from backpy.core.space.backup_space import BackupSpace

palette = get_default_palette()

__all__ = ["Schedule"]


class Schedule:
    def __init__(
        self,
        unique_id: uuid.UUID,
        backup_space: BackupSpace,
        location: str,
        include: list[str],
        exclude: list[str],
        time_pattern: str,
        description: str,
    ):
        self._uuid: uuid.UUID = unique_id
        self._backup_space: BackupSpace = backup_space
        self._location: str = location
        self._include: list[str] = include
        self._exclude: list[str] = exclude
        self._time_pattern: str = time_pattern
        self._description: str = description
        self._config: TOMLConfiguration = TOMLConfiguration(
            path=Path(VariableLibrary.get_variable("paths.schedule_directory"))
            / (str(self._uuid) + ".toml"),
            create_if_not_exists=True,
        )

    def activate(self) -> None:
        cron = crontab.CronTab(user=True)
        job = cron.new(command=self.get_command(), comment=self._get_comment())
        job.setall(self._time_pattern)
        cron.write()

    def deactivate(self):
        for job in self._get_cronjobs():
            job.delete()
            job.cron.write()

    def delete(self, verbosity_level: int = 1):
        if self.is_active():
            self.deactivate()
            if verbosity_level > 1:
                print(f"Deleted cronjobs for schedule {self._uuid}")

        self.get_config().get_path().unlink()
        if verbosity_level > 1:
            print(f"Deleted config for schedule {self._uuid}")

    def update_config(self):
        current_content = self._config.as_dict()

        content = {
            "uuid": str(self._uuid),
            "backup_space": str(self._backup_space.get_uuid()),
            "location": self._location,
            "include": self._include,
            "exclude": self._exclude,
            "time_pattern": self._time_pattern,
            "description": self._description,
        }

        self._config.dump_dict(dict(merge({}, current_content, content)))

    def get_info_table(self, include_command: bool = False) -> Table:
        table = Table(
            title=f"{palette.pink}SCHEDULE INFORMATION{RESET}",
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
        active = self.is_active()
        table.add_row(
            f"{palette.sky}Active",
            f"{palette.green if active else palette.red}{active}",
        )
        table.add_row(
            f"{palette.sky}Backup Space",
            f"{palette.base}{self._backup_space.get_name()} "
            f"(UUID: {self._backup_space.get_uuid()})",
        )

        table.add_row(f"{palette.sky}Location", f"{palette.base}{self._location}")
        table.add_row(f"{palette.sky}Include", f"{palette.base}{self._include}")
        table.add_row(f"{palette.sky}Exclude", f"{palette.base}{self._exclude}")

        table.add_row(
            f"{palette.sky}Time Pattern", f"{palette.base}{self._time_pattern}"
        )
        table.add_row(f"{palette.sky}Description", f"{palette.base}{self._description}")

        if include_command:
            table.add_row(
                f"{palette.sky}Command", f"{palette.base}{self.get_command()}"
            )

        return table

    def _get_cronjobs(self) -> list[crontab.CronItem]:
        return list(crontab.CronTab(user=True).find_comment(self._get_comment()))

    def _get_comment(self) -> str:
        return str(self._uuid) + " " + COMMENT_SUFFIX

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_uuid(cls, unique_id: str) -> "Schedule":

        from backpy.core.space.backup_space import BackupSpace

        config = TOMLConfiguration(
            path=Path(VariableLibrary.get_variable("paths.schedule_directory"))
            / (unique_id + ".toml")
        )
        if not config.is_valid():
            raise InvalidScheduleError("There is no schedule with this UUID.")

        return cls(
            unique_id=uuid.UUID(unique_id),
            backup_space=BackupSpace.load_by_uuid(unique_id=config["backup_space"]),
            location=config["location"],
            include=config["include"],
            exclude=config["exclude"],
            time_pattern=config["time_pattern"],
            description=config["description"],
        )

    @classmethod
    def get_schedules(cls, active: bool = False) -> list[Schedule]:
        schedules = []
        for tomlf in Path(
            VariableLibrary.get_variable("paths.schedule_directory")
        ).glob("*.toml"):
            try:
                schedule = Schedule.load_by_uuid(unique_id=tomlf.stem)
                if active and not schedule.is_active():
                    continue
                schedules.append(schedule)

            except InvalidScheduleError:
                continue

        return schedules

    @classmethod
    def load_by_backup_space(
        cls, backup_space: BackupSpace, active: bool = False
    ) -> list["Schedule"]:
        schedules = []
        for schedule in Schedule.get_schedules(active=active):
            if schedule.get_backup_space().get_uuid() == backup_space.get_uuid():
                schedules.append(schedule)

        return schedules

    @classmethod
    def create_from_backup_space(
        cls,
        backup_space: BackupSpace,
        time_pattern: str,
        description: str,
        exclude: list[str],
        include: list[str],
        location: str,
        verbosity_level: int = 1,
    ):

        if location not in ["local", "remote", "all"]:
            raise ValueError("The location must be either 'local', 'remote' or 'all'.")

        unique_id = uuid.uuid4()

        cls = cls(
            unique_id=unique_id,
            backup_space=backup_space,
            location=location,
            include=include,
            exclude=exclude,
            time_pattern=time_pattern,
            description=description,
        )

        cls.update_config()

        if verbosity_level > 1:
            print(f"Created schedule '{cls._uuid}' with command '{cls.get_command()}'.")

        return cls

    #####################
    #       GETTER      #
    #####################

    def get_uuid(self) -> uuid.UUID:
        return self._uuid

    def get_backup_space(self) -> BackupSpace:
        return self._backup_space

    def get_description(self) -> str:
        return self._description

    def get_location(self) -> str:
        return self._location

    def get_exclude(self) -> list[str]:
        return self._exclude

    def get_include(self) -> list[str]:
        return self._include

    def get_command(self) -> str:
        command = (
            f"backpy backup create {self._backup_space.get_uuid()} "
            f'--location "{self._location}" '
            f'--comment "Scheduled backup (Schedule-UUID: {self._uuid})"'
        )

        for exclusion in self._exclude:
            command += f' -X "{exclusion}"'

        for inclusion in self._include:
            command += f' -I "{inclusion}"'

        command = command.split(" ")

        if command[0] == "backpy":
            command[0] = str(Path(sys.executable).parent / "backpy")

        return " ".join(command)

    def get_time_pattern(self) -> str:
        return self._time_pattern

    def is_active(self) -> bool:
        return len(self._get_cronjobs()) > 0

    def get_config(self) -> TOMLConfiguration:
        return self._config
