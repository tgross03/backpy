from pathlib import Path

import toml


def _parse_key(key: str):
    key_components = key.split(".")
    return key_components


class TOMLConfiguration:
    def __init__(self, path: str | Path, create_if_not_exists: bool = False):
        self._path: Path = Path(path) if isinstance(path, str) else path

        if self._path.suffix != ".toml":
            raise TypeError("The given configuration file has to be a TOML file!")

        if create_if_not_exists:
            self._path.parent.mkdir(exist_ok=True, parents=True)
            self._path.touch(exist_ok=True)

    def __getitem__(self, item: str):
        if not self._path.is_file():
            raise FileNotFoundError(
                "The variable configuration could not be "
                f"found at location {str(self._path)}!"
            )

        keys = _parse_key(item)
        content_dict = toml.load(self._path)

        content = content_dict
        for key in keys:
            if isinstance(content, dict):
                content = content[key]
            else:
                raise KeyError(
                    f"The key component '{key}' is set to a non-dict value and "
                    "therefore there cannot be a child value!"
                )

        return content

    def __setitem__(self, key: str, value: str):
        if not self._path.is_file():
            raise FileNotFoundError(
                "The variable configuration could not "
                f"be found at location {str(self._path)}!"
            )

        keys = _parse_key(key)
        content_dict = toml.load(self._path)

        content = content_dict
        for i in range(len(keys)):
            key = keys[i]

            if i < len(keys) - 1:
                if key not in content:
                    content[key] = dict()
                else:
                    if isinstance(content[key], dict):
                        content = content[key]
                    else:
                        raise KeyError(
                            f"The key component '{key}' is already "
                            "set to a non-dict value!"
                        )
            else:
                content[key] = value

        with open(self._path, "w") as file:
            toml.dump(o=content_dict, f=file)

    def __contains__(self, item: str):
        try:
            self[item]
        except KeyError:
            return False
        return True

    def dump_dict(self, content: dict):
        with open(self._path, "w") as file:
            toml.dump(o=content, f=file)

    def as_dict(self):
        return toml.load(self._path)
