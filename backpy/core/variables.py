from pathlib import Path

from mergedeep import merge

import backpy


class VariableLibrary:
    def __init__(self):
        self._path: Path = (
            Path(backpy.__file__).parent.parent / ".config/variables.toml"
        )
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
            },
        }

        self._config.dump_dict(
            content if regenerate else dict(merge({}, content, current_content))
        )
        self._config.prepend_no_edit_warning()

    def get_variable(self, key: str):
        return self._config[key]

    def set_variable(self, key: str, value: str) -> None:
        self._config[key] = value

    def exists(self) -> bool:
        return self._config.is_valid()
