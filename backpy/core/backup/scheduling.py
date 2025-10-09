import sys
import uuid
from pathlib import Path

import crontab
from mergedeep import merge

from backpy import TOMLConfiguration, VariableLibrary
from backpy.core.backup.backup_space import BackupSpace
from backpy.core.utils.exceptions import InvalidScheduleError

COMMENT_SUFFIX = "(MANAGED BY BACKPY)"


class Schedule:
    def __init__(
        self,
        unique_id: uuid.UUID,
        backup_space: BackupSpace,
        command: str,
        time_pattern: str,
        description: str,
    ):
        self._uuid: uuid.UUID = unique_id
        self._backup_space: BackupSpace = backup_space
        self._command: str = command
        self._time_pattern: str = time_pattern
        self._description: str = description
        self._config: TOMLConfiguration = TOMLConfiguration(
            path=Path(VariableLibrary().get_variable("paths.schedule_directory"))
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
            "command": self._command,
            "time_pattern": self._time_pattern,
            "description": self._description,
        }

        self._config.dump_dict(dict(merge({}, current_content, content)))

    def _get_cronjobs(self) -> list[crontab.CronItem]:
        return list(crontab.CronTab(user=True).find_comment(self._get_comment()))

    def _get_comment(self) -> str:
        return str(self._uuid) + " " + COMMENT_SUFFIX

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_uuid(cls, unique_id: str) -> "Schedule":
        config = TOMLConfiguration(
            path=Path(VariableLibrary().get_variable("paths.schedule_directory"))
            / (unique_id + ".toml")
        )
        if not config.is_valid():
            raise InvalidScheduleError("There is no schedule with this UUID.")

        return cls(
            unique_id=uuid.UUID(unique_id),
            command=config["command"],
            time_pattern=config["time_pattern"],
        )

    @classmethod
    def load_by_backup_space(cls, backup_space: BackupSpace) -> list["Schedule"]:
        schedules = []
        for tomlf in Path(VariableLibrary().get_variable("paths.schedule_directory")).glob(
            "*.toml"
        ):
            try:
                schedule = Schedule.load_by_uuid(unique_id=tomlf.stem)
                if schedule.get_backup_space() == backup_space:
                    schedules.append(schedule)

            except InvalidScheduleError:
                pass

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
        activate: bool,
        verbosity_level: int = 1,
    ):

        if location not in ["local", "remote", "all"]:
            raise ValueError("The location must be either 'local', 'remote' or 'all'.")

        unique_id = uuid.uuid4()

        command = (
            f"backpy backup create {backup_space.get_name()} "
            f'--location "{location}" '
            f'--comment "Scheduled backup (Schedule-UUID: {unique_id})"'
        )

        for exclusion in exclude:
            command += f' -X "{exclusion}"'

        for inclusion in include:
            command += f' -I "{inclusion}"'

        cls = cls(
            unique_id=unique_id,
            backup_space=backup_space,
            command=command,
            time_pattern=time_pattern,
            description=description,
        )

        cls.update_config()

        if verbosity_level > 1:
            print(f"Created schedule '{cls._uuid}' with command '{cls._command}'.")

        if activate:
            cls.activate()

            if verbosity_level > 1:
                print(f"Activated schedule '{cls._uuid}'.")

        return cls

    #####################
    #       GETTER      #
    #####################

    def get_uuid(self) -> uuid.UUID:
        return self._uuid

    def get_backup_space(self) -> BackupSpace:
        return self._backup_space

    def get_command(self) -> str:
        command = self._command.split(" ")

        if command[0] == "backpy":
            command[0] = str(Path(sys.executable).parent / "backpy")

        return " ".join(command)

    def get_time_pattern(self) -> str:
        return self._time_pattern

    def is_active(self) -> bool:
        return len(self._get_cronjobs()) > 0

    def get_config(self) -> TOMLConfiguration:
        return self._config
