from pathlib import Path

import backpy


class VariableLibrary:
    def __init__(self):
        self._path: Path = (
            Path(backpy.__file__).parent.parent / ".config/variables.toml"
        )
        self._config = backpy.TOMLConfiguration(self._path, create_if_not_exists=True)

    def generate(self, regenerate: bool = False):
        self._path.parent.mkdir(exist_ok=True, parents=True)

        if regenerate:
            self._path.unlink(missing_ok=True)

        self._path.touch(exist_ok=True)

        content = {
            "config_path": str(
                Path(backpy.__file__).parent.parent / ".config/config.toml"
            ),
            "backup_directory": str(
                Path(backpy.__file__).parent.parent / ".backups/config.toml"
            ),
        }

        self._config.dump_dict(content)

    def get_variable(self, key: str):
        return self._config[key]

    def set_variable(self, key: str, value: str):
        self._config[key] = value
