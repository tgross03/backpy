import tomllib
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Any

import tomli_w

from backpy.core.utils.exceptions import InvalidTOMLConfigurationError

__all__ = ["TOMLConfiguration", "MissingKeyPolicy"]


class MissingKeyPolicy(Enum):
    ERROR = 1
    RETURN_NONE = 2


class TOMLConfiguration:
    def __init__(
        self,
        path: PathLike | str,
        create_if_not_exists: bool = False,
        missing_key_policy: MissingKeyPolicy = MissingKeyPolicy.ERROR,
    ):
        """
        Initializes a new TOML configuration.

        Parameters
        ----------

        path : PathLike | str
            The path to the toml file.

        create_if_not_exists : bool, optional
            Whether to create the corresponding file if it does not exist.
            Default is ``False``.

        missing_key_policy : MissingKeyPolicy | str, optional
            The policy to react to missing keys.
            Default is ``MissingKeyPolicy.ERROR`` meaning that an error will be raised.

        """

        self._path: Path = Path(path)

        if self._path.suffix.lower() != ".toml":
            raise InvalidTOMLConfigurationError(
                "The given file has an incorrect file suffix "
                f"(is '{self._path.suffix}')! Has to be 'toml'"
            )

        if not self.exists() and create_if_not_exists:
            self.create()

        self._missing_key_policy: MissingKeyPolicy = (
            missing_key_policy
            if isinstance(missing_key_policy, MissingKeyPolicy)
            else MissingKeyPolicy[missing_key_policy]
        )

    def create(self) -> None:
        """
        Creates an empty TOML file at the config path.
        """

        self._path.parent.mkdir(exist_ok=True, parents=True)
        self._path.touch(exist_ok=True)

    def exists(self) -> bool:
        """
        Checks whether the file exists.

        Returns
        -------

        bool : Whether the file exists.
        """
        return self._path.exists() and self._path.is_file()

    def __getitem__(self, key: str) -> Any:
        content = self.asdict()

        keys = key.split(".")

        for key in keys:
            if not isinstance(content, dict) or key not in content:
                return self._handle_missing_key(key=key)

            content = content[key]

        return content

    def _handle_missing_key(self, key: str) -> None:
        match self._missing_key_policy:
            case MissingKeyPolicy.ERROR:
                raise KeyError(f"Invalid key: '{key}'")
            case MissingKeyPolicy.RETURN_NONE:
                return None

    def __setitem__(self, key: str, value: Any) -> None:
        content = self.asdict()

        keys = key.split(".")

        content_dict = content
        for kidx, key in zip(range(len(keys)), keys):
            if not isinstance(content_dict, dict):
                raise KeyError(f"Invalid key: '{key}'")

            if kidx == len(keys) - 1:
                if key in content_dict:
                    if (
                        isinstance(content_dict[key], dict)
                        and not isinstance(value, dict)
                    ) or (
                        isinstance(value, dict)
                        and not isinstance(content_dict[key], dict)
                    ):
                        raise TypeError(
                            "The type of the value that to be set must be the "
                            "same of the current value!"
                        )

                if value is not None:
                    content_dict[key] = value
                else:
                    del content_dict[key]
            else:
                content_dict = content_dict[key]

        with open(self._path, "wb") as tomlf:
            tomli_w.dump(content, tomlf)

    def __contains__(self, key: str) -> bool:
        if not self.exists():
            return False

        content = self.asdict()
        keys = key.split(".")

        for key in keys:
            if key not in content:
                return False

            content = content[key]

        return True

    def get_keys(self, non_dict_only: bool = False) -> list[str]:
        """
        Provides a list of all keys in the configuration file.

        Parameters
        ----------

        non_dict_only : bool, optional
            Whether only to show the keys for variables and not for
            sections of the configuration file.
            Default is ``True``.

        Returns
        -------

        list[str] : A list of keys in the file.

        """

        def recursive_keys(dictionary: dict, parent: str | None = None) -> list[str]:
            keys = []
            for key, value in dictionary.items():
                parent_key = f"{parent}.{key}" if parent is not None else key
                if isinstance(value, dict):
                    if not non_dict_only:
                        keys.append(key)
                    keys.extend(recursive_keys(dictionary=value, parent=parent_key))
                else:
                    keys.append(parent_key)
            return keys

        return recursive_keys(dictionary=self.asdict())

    def asdict(self) -> dict[str, Any]:
        """
        Provides the content of the TOML file as a dictionary.

        Returns
        -------

        dict : The content of the TOML file.
        """
        with open(self._path, "rb") as tomlf:
            content = tomllib.load(tomlf)

        return content

    def dump(self, content: dict[str, Any]) -> None:
        """
        Dumps the given dictionary as content into the TOML file.

        Parameters
        ----------

        content : dict
            The content to dump into the file.
        """
        with open(self._path, "wb") as tomlf:
            tomli_w.dump(content, tomlf)
