import uuid
from pathlib import Path

from backpy import VariableLibrary


class Backup:
    def __init__(self, name: str):
        self._uuid: uuid.UUID = uuid.uuid4()
        self._name: str = name
        self._dir: Path = Path(VariableLibrary()["backup_directory"]) / str(self._uuid)

    def restore_state(self, uuid: uuid.UUID):
        raise NotImplementedError("This method is abstract and has to be overriden!")

    def create_state(self):
        None


class BackupState:
    def __init__(self, backup: Backup):
        self._backup: Backup = backup


class FileBackup(Backup):
    def __init__(self, path: str, exclude_paths: list[str] | None = None):
        self._uuid: uuid.UUID = uuid.uuid4()
        self._origin_path: Path = Path(path)

        if exclude_paths is None:
            exclude_paths = []
        self._exclude: list[Path] = [
            Path(exclude_path) for exclude_path in exclude_paths
        ]
