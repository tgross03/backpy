import uuid
from pathlib import Path

import crontab
from mergedeep import merge

from backpy import TOMLConfiguration, VariableLibrary
from backpy.core.backup.backup_space import BackupSpace
from backpy.core.utils.exceptions import InvalidScheduleError

COMMENT_SUFFIX = "(MANAGED BY BACKPY)"
cron = crontab.CronTab(user=True)


class Schedule:
    def __init__(self, unique_id: uuid.UUID, command: str, time_pattern: str):
        self._uuid: uuid.UUID = unique_id
        self._command: str = command
        self._time_pattern: str = time_pattern
        self._cron_items: list[crontab.CronItem] = self._get_cronjobs()
        self._active: bool = len(self._cron_items) > 0
        self._config: TOMLConfiguration = TOMLConfiguration(
            path=Path(VariableLibrary().get_variable("paths.schedule_directory"))
            / (str(self._uuid) + ".toml")
        )

    def activate(self):
        job = cron.new(command=self._command, comment=self._get_comment())
        job.setall(self._time_pattern)
        cron.write()
        self._active = True
        return job

    def deactivate(self):
        for job in self._get_cronjobs():
            job.delete()
        self._active = False

    def update_config(self):
        current_content = self._config.as_dict()

        content = {
            "uuid": str(self._uuid),
            "command": self._command,
            "time_pattern": self._time_pattern,
        }

        self._config.dump_dict(dict(merge({}, current_content, content)))

    def _get_cronjobs(self) -> list[crontab.CronItem]:
        return list(cron.find_comment(self._get_comment()))

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
    def create_from_backup_space(
        cls,
        backup_space: BackupSpace,
        time_pattern: str,
        exclude: list[str],
        include: list[str],
        location: str,
        activate: bool,
        verbosity_level: int = 1,
    ):

        if location not in ["local", "remote", "all"]:
            raise ValueError("The location must be either 'local', 'remote' or 'all'.")

        command = (
            f"backpy backup create {backup_space.get_name()} "
            f"--location {location} "
            # f"--comment {}"
        )

        for exclusion in exclude:
            command += f" -X {exclusion}"

        for inclusion in include:
            command += f" -I {inclusion}"

        cls = cls(
            unique_id=uuid.uuid4(),
            command=command,
            time_pattern=time_pattern,
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

    def get_command(self) -> str:
        return self._command

    def get_time_pattern(self) -> str:
        return self._time_pattern

    def is_active(self) -> bool:
        return self._active

    def get_config(self) -> TOMLConfiguration:
        return self._config
