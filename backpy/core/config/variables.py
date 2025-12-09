from pathlib import Path

from mergedeep import merge

import backpy
from backpy.core.config.configuration import TOMLConfiguration


class VariableLibrary:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._path: Path = Path.home() / ".backpy/config/variables.toml"
        self._config = backpy.TOMLConfiguration(self._path, create_if_not_exists=True)

        self.generate(regenerate=False)

    def generate(self, regenerate: bool = False) -> None:

        self._path.parent.mkdir(exist_ok=True, parents=True)

        if regenerate:
            self._path.unlink(missing_ok=True)

        if not self.exists():
            self._path.touch()

        current_content = self._config.as_dict()

        content = {
            "paths": {
                "backup_directory": str(Path.home() / ".backpy/backups"),
                "remote_directory": str(Path.home() / ".backpy/remotes"),
                "schedule_directory": str(Path.home() / ".backpy/schedules"),
                "temporary_directory": str(Path.home() / ".backpy/.temp"),
            },
            "backup": {
                "states": {
                    "default_compression_algorithm": "zip",
                    "default_compression_level": 6,
                    "default_remote_root_dir": ".backpy",
                    "default_sha256_cmd": "sha256sum",
                }
            },
            "cli": {
                "color_palette": "latte",
                "rich": {"palette": "solarized", "style": "box"},
            },
        }

        self._config.dump_dict(
            content if regenerate else dict(merge({}, content, current_content))
        )
        self._config.prepend_no_edit_warning()

    @classmethod
    def get_config(cls) -> TOMLConfiguration:
        instance = cls()
        return instance._config

    @classmethod
    def get_path(cls) -> Path:
        instance = cls()
        return instance._path

    @classmethod
    def get_variable(cls, key: str):
        instance = cls()
        return instance._config[key]

    @classmethod
    def set_variable(cls, key: str, value: str) -> None:
        instance = cls()
        instance._config[key] = value

    @classmethod
    def exists(cls) -> bool:
        instance = cls()
        return instance._config.is_valid()
