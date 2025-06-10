import uuid
from pathlib import Path


class Backup:
    def __init__(self):
        None


class FileBackup:
    def __init__(self, path: str, exclude_paths: list[str] | None = None):

        self._uuid: uuid.UUID = uuid.uuid4()
        self._origin_path: Path = Path(path)

        if exclude_paths is None:
            exclude_paths = []
        self._exclude: list[Path] = [
            Path(exclude_path) for exclude_path in exclude_paths
        ]
