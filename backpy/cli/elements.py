import getpass
from collections.abc import Callable
from pathlib import Path

from fuzzyfinder import fuzzyfinder

from backpy import Backup, BackupSpace
from backpy.cli.colors import EFFECTS, RESET, get_default_palette
from backpy.core.remote import Remote, get_remotes

palette = get_default_palette()


def print_error_message(error: Exception, debug: bool) -> None:
    if debug:
        raise error
    else:
        print(f"{palette.red}ERROR: {palette.maroon}{error.args[0]}{RESET}")


def _validate_always(value: str) -> bool:
    return True


def _validate_not_none(value: str) -> bool:
    return value is not None


def _validate_file_path(value: str) -> bool:
    return Path(value).expanduser().is_file(follow_symlinks=True)


def _validate_directory_path(value: str) -> bool:
    return Path(value).expanduser().is_dir(follow_symlinks=True)


def _validate_integer(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False

    return True


def _validate_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False

    return True


class ConfirmInput:
    def __init__(self, message: str, default_value: bool) -> None:
        self.message: str = message
        self.default_value: bool = default_value

    def _get_default_input(self) -> str:
        if self.default_value:
            return "y"
        else:
            return "n"

    def _get_suffix(self) -> str:
        true_str = "Y" if self.default_value else "y"
        false_str = "N" if not self.default_value else "n"
        return f"({true_str}/{false_str})"

    def _get_prompt(self) -> str:
        return f"{self.message} {self._get_suffix()} "

    def prompt(self) -> bool:
        confirmation = None
        valid_input = False

        while not valid_input:
            in_value = input(self._get_prompt())

            if in_value.lower() != "y" and in_value.lower() != "n" and in_value != "":
                print(
                    f"{palette.maroon}You have type y, n or nothing to proceed!{RESET}"
                )
                continue

            confirmation = (in_value or self._get_default_input().lower()) == "y"
            valid_input = True

        return confirmation


class TextInput:
    def __init__(
        self,
        message: str,
        default_value: str | None = None,
        allow_none: bool = False,
        validate: Callable[[str], bool] = _validate_always,
        suggest_matches: bool = False,
        case_sensitive: bool = True,
        suggestible_values: list[str] | None = None,
        confirm_suggestion: bool = True,
        highlight_suggestion: bool = True,
        invalid_error_message: str | None = None,
    ):
        self.message: str = message
        self.default_value: str | None = default_value
        self.allow_none: bool = allow_none
        self._validate: Callable[[str], bool] = validate
        self.suggest_matches: bool = suggest_matches
        self.case_sensitive: bool = case_sensitive
        self.suggestible_values: list[str] = (
            [] if suggestible_values is None else suggestible_values
        )
        self.confirm_suggestion: bool = confirm_suggestion
        self.highlight_suggestion: bool = highlight_suggestion
        self.invalid_error_message: str = (
            invalid_error_message
            if invalid_error_message
            else f"{palette.red}Invalid input! Please try again.{RESET}"
        )

    def _get_prompt(self) -> str:
        return f"{self.message}" + (
            f" (default: '{self.default_value}') "
            if self.default_value is not None
            else " "
        )

    def prompt(self) -> str | None:

        valid_result = False

        value = None

        while not valid_result:
            value = input(self._get_prompt())

            if value == "":
                value = self.default_value

            if value is None and self.allow_none:
                return value

            valid_input = self._validate(value)

            if not valid_input:
                print(
                    f"{palette.red}ERROR: {palette.maroon}"
                    f"{self.invalid_error_message.format(value=value)}{RESET}"
                )
                continue

            if self.suggest_matches:
                matched = list(fuzzyfinder(value, self.suggestible_values))

                if len(matched) == 0:
                    print(
                        f"{palette.red}ERROR: {palette.maroon}"
                        f"{self.invalid_error_message.format(value=value)}{RESET}"
                    )
                    continue

                if self.case_sensitive:
                    if matched[0] == value:
                        break
                else:
                    if matched[0].lower() == value.lower():
                        break

                best_match = list(
                    fuzzyfinder(
                        value,
                        self.suggestible_values,
                        highlight=self.highlight_suggestion,
                    )
                )[0]

                if self.confirm_suggestion:
                    valid_result = ConfirmInput(
                        message=(
                            f"{palette.base}Did you mean "
                            f"{best_match}"
                            f"{palette.base}?{RESET}"
                        ),
                        default_value=True,
                    ).prompt()
                else:
                    valid_result = True

                value = matched[0]
            else:
                valid_result = True

        return value


class PasswordInput:
    def __init__(
        self,
        message: str,
        allow_empty: bool,
        confirm_input: bool,
        default_value: str | None = None,
    ):
        self.message: str = message
        self.allow_empty: bool = allow_empty
        self.confirm_input: bool = confirm_input
        self.default_value: str | None = default_value

    def prompt(self) -> str:

        password = None
        valid_input = False

        while not valid_input:
            password_input: str = getpass.getpass(
                prompt=f"{self.message} {'(again) ' if password is not None else ''}"
            )

            if (
                password is not None
                and password != password_input
                and self.confirm_input
            ):
                password = None
                print(
                    f"{palette.red}ERROR: {palette.maroon}The two passwords were not identical. "
                    f"Try again!{RESET}"
                )
                continue

            if password_input == "" and not self.allow_empty:
                print(
                    f"{palette.red}ERROR: {palette.maroon}The password may not be empty!{RESET}"
                )
                continue

            if password is None and self.confirm_input:
                password = password_input
                continue

            password = password_input
            valid_input = True

        return password


class BackupSpaceInput(TextInput):
    def __init__(
        self,
        validate: Callable[[str], bool] = _validate_always,
        suggest_matches: bool = False,
        case_sensitive: bool = True,
        confirm_suggestion: bool = True,
        highlight_suggestion: bool = True,
    ):

        spaces = BackupSpace.get_backup_spaces()

        if len(spaces) == 0:
            print(
                f"{palette.red}ERROR: {palette.maroon}There is no valid Backup Space present. "
                f"You have to create a Backup Space first. Use 'backpy --help' for help.{RESET}"
            )
            return

        space_names_uuids = []

        for space in spaces:
            space_names_uuids.append(str(space.get_uuid()))
            space_names_uuids.append(space.get_name())

        super().__init__(
            message=f"{palette.base}> Enter the {palette.lavender}name{palette.base} "
            f"or {palette.lavender}UUID{palette.base} of the {EFFECTS.underline.on}"
            f"Backup Space{RESET}{palette.base}: ",
            invalid_error_message=f"{palette.maroon}There is no Backup Space with "
            f"{palette.red}name{palette.maroon} "
            f"or {palette.red}UUID {EFFECTS.reverse.on}{palette.peach}"
            "{value}"
            f"{EFFECTS.reverse.off}"
            f"{palette.maroon}. Please try again!{RESET}",
            validate=validate,
            suggest_matches=suggest_matches,
            suggestible_values=space_names_uuids,
            case_sensitive=case_sensitive,
            confirm_suggestion=confirm_suggestion,
            highlight_suggestion=highlight_suggestion,
        )

    def prompt(self) -> BackupSpace:
        result = super().prompt()
        try:
            space = BackupSpace.load_by_uuid(result)
        except Exception:
            space = BackupSpace.load_by_name(result)

        return space.get_type().child_class.load_by_uuid(
            unique_id=str(space.get_uuid())
        )


class BackupInput(TextInput):
    def __init__(
        self,
        backup_space: BackupSpace,
        check_hash: bool = True,
        validate: Callable[[str], bool] = _validate_always,
        suggest_matches: bool = False,
        case_sensitive: bool = True,
        confirm_suggestion: bool = True,
        highlight_suggestion: bool = True,
    ):

        self.backup_space: BackupSpace = backup_space
        self.check_hash: bool = check_hash
        backups = backup_space.get_backups(check_hash=False)

        if len(backups) == 0:
            print(
                f"{palette.maroon}There is no valid Backup created for this Backup Space. "
                f"You have to create a Backup first. Use 'backpy --help' for help.{RESET}"
            )
            return

        backup_uuids = []

        for backup in backups:
            backup_uuids.append(str(backup.get_uuid()))

        backup_uuids.extend(["oldest", "newest", "largest", "smallest"])

        super().__init__(
            message=f"{palette.base}> Enter the {palette.lavender}UUID{palette.base} "
            f"of the {EFFECTS.underline.on}"
            f"Backup{RESET}{palette.base}: ",
            invalid_error_message=f"{palette.maroon}There is no Backup with "
            f"the {palette.red}UUID {EFFECTS.reverse.on}{palette.peach}"
            "{value}"
            f"{EFFECTS.reverse.off}"
            f"{palette.maroon}. Please try again!{RESET}",
            validate=validate,
            suggest_matches=suggest_matches,
            suggestible_values=backup_uuids,
            case_sensitive=case_sensitive,
            confirm_suggestion=confirm_suggestion,
            highlight_suggestion=highlight_suggestion,
        )

    def prompt(self) -> Backup:
        result = super().prompt()

        match result:
            case "oldest":
                return self.backup_space.get_backups(sort_by="date", check_hash=False)[
                    -1
                ]
            case "newest":
                return self.backup_space.get_backups(sort_by="date", check_hash=False)[
                    0
                ]
            case "largest":
                return self.backup_space.get_backups(sort_by="size", check_hash=False)[
                    0
                ]
            case "smallest":
                return self.backup_space.get_backups(sort_by="size", check_hash=False)[
                    -1
                ]
            case _:
                return Backup.load_by_uuid(
                    backup_space=self.backup_space,
                    unique_id=result,
                    check_hash=self.check_hash,
                )


class RemoteInput(TextInput):
    def __init__(
        self,
        validate: Callable[[str], bool] = _validate_always,
        default_value: str | None = None,
        allow_none: bool = False,
        suggest_matches: bool = False,
        case_sensitive: bool = True,
        confirm_suggestion: bool = True,
        highlight_suggestion: bool = True,
    ):

        remotes = get_remotes()

        remote_names_uuids = []

        for remote in remotes:
            remote_names_uuids.append(str(remote.get_uuid()))
            remote_names_uuids.append(remote.get_name())

        super().__init__(
            message=f"{palette.base}> Enter the {palette.lavender}name{palette.base} "
            f"or {palette.lavender}UUID{palette.base} of the {EFFECTS.underline.on}"
            f"Remote{RESET}{palette.base} to which the backups should be saved: ",
            invalid_error_message=f"{palette.maroon}There is no Remote with "
            f"{palette.red}name{palette.maroon} "
            f"or {palette.red}UUID {EFFECTS.reverse.on}{palette.peach}"
            "{value}"
            f"{EFFECTS.reverse.off}"
            f"{palette.maroon}. Please try again!{RESET}",
            validate=validate,
            default_value=default_value,
            allow_none=allow_none,
            suggest_matches=suggest_matches,
            suggestible_values=remote_names_uuids,
            case_sensitive=case_sensitive,
            confirm_suggestion=confirm_suggestion,
            highlight_suggestion=highlight_suggestion,
        )

    def prompt(self) -> Remote | None:
        result = super().prompt()

        if result is None and self.allow_none:
            return None

        try:
            remote = Remote.load_by_uuid(result)
        except Exception:
            remote = Remote.load_by_name(result)

        return remote


class EnumerationInput(TextInput):
    def __init__(
        self,
        message: str,
        default_value: str | None = None,
        allow_none: bool = False,
        validate: Callable[[str], bool] = _validate_always,
        invalid_error_message: str | None = None,
    ):
        super().__init__(
            message=message,
            default_value=default_value,
            allow_none=allow_none,
            validate=validate,
            invalid_error_message=(
                invalid_error_message
                if invalid_error_message
                else f"{palette.maroon}Invalid enumeration input! Enumerations "
                f"have to have follow this syntax: "
                f"{palette.peach}{EFFECTS.reverse.on}val1,val2,val3 "
                f"{EFFECTS.reverse.off}{palette.maroon}Please try again.{RESET}"
            ),
        )

    def prompt(self) -> list[str] | None:
        prompt = super().prompt()

        if prompt is None and self.allow_none:
            return None

        prompt = prompt.split(",")

        if prompt == [""] or prompt is None:
            return []
        else:
            return prompt


class FilePathInput(TextInput):
    def __init__(
        self,
        message: str,
        default_value: str | None = None,
        allow_none: bool = False,
        validate: Callable[[str], bool] = _validate_file_path,
        invalid_error_message: str | None = None,
    ):
        super().__init__(
            message=message,
            default_value=default_value,
            allow_none=allow_none,
            validate=validate,
            invalid_error_message=(
                invalid_error_message
                if invalid_error_message
                else f"{palette.maroon}Invalid file path input! Please try again.{RESET}"
            ),
        )

    def prompt(self) -> Path | None:
        prompt = super().prompt()

        if prompt is None and self.allow_none:
            return None

        return Path(prompt)


class DirectoryPathInput(TextInput):
    def __init__(
        self,
        message: str,
        default_value: str | None = None,
        allow_none: bool = False,
        validate: Callable[[str], bool] = _validate_directory_path,
        invalid_error_message: str | None = None,
    ):
        super().__init__(
            message=message,
            default_value=default_value,
            allow_none=allow_none,
            validate=validate,
            invalid_error_message=(
                invalid_error_message
                if invalid_error_message
                else f"{palette.maroon}Invalid directory path input! Please try again.{RESET}"
            ),
        )

    def prompt(self) -> Path | None:
        prompt = super().prompt()

        if prompt is None and self.allow_none:
            return None

        return Path(prompt)


class IntegerInput(TextInput):
    def __init__(
        self,
        message: str,
        default_value: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
        allow_none: bool = False,
        validate: Callable[[str], bool] = _validate_integer,
        suggest_matches: bool = False,
        suggestible_values: list[int] | None = None,
        confirm_suggestion: bool = True,
        highlight_suggestion: bool = True,
        invalid_error_message: str | None = None,
    ):

        suggestible_values = [] if not suggestible_values else suggestible_values
        self._min_value: int | None = min_value
        self._max_value: int | None = max_value

        super().__init__(
            message=message,
            default_value=str(default_value) if default_value else None,
            allow_none=allow_none,
            validate=validate,
            suggest_matches=suggest_matches,
            case_sensitive=False,
            suggestible_values=[str(val) for val in suggestible_values],
            confirm_suggestion=confirm_suggestion,
            highlight_suggestion=highlight_suggestion,
            invalid_error_message=(
                invalid_error_message
                if invalid_error_message
                else f"{palette.maroon}Invalid integer number input! Please try again.{RESET}"
            ),
        )

    def prompt(self) -> int | None:

        prompt = super().prompt()

        if prompt is None and self.allow_none:
            return None

        value = int(prompt)

        if self._max_value is not None and value > self._max_value:
            print(
                f"{palette.red}ERROR: {palette.maroon}"
                f"The given value is too large! Maximum: {self._max_value}{RESET}"
            )
            return self.prompt()

        if self._min_value is not None and value < self._min_value:
            print(
                f"{palette.red}ERROR: {palette.maroon}"
                f"The given value is too small! Minimum: {self._max_value}{RESET}"
            )
            return self.prompt()

        return value


class FloatInput(TextInput):
    def __init__(
        self,
        message: str,
        default_value: float | None = None,
        allow_none: bool = False,
        validate: Callable[[str], bool] = _validate_float,
        suggest_matches: bool = False,
        suggestible_values: list[float] | None = None,
        confirm_suggestion: bool = True,
        highlight_suggestion: bool = True,
        invalid_error_message: str | None = None,
    ):

        suggestible_values = [] if not suggestible_values else suggestible_values

        super().__init__(
            message=message,
            default_value=str(default_value) if default_value else None,
            allow_none=allow_none,
            validate=validate,
            suggest_matches=suggest_matches,
            case_sensitive=False,
            suggestible_values=[str(val) for val in suggestible_values],
            confirm_suggestion=confirm_suggestion,
            highlight_suggestion=highlight_suggestion,
            invalid_error_message=(
                invalid_error_message
                if invalid_error_message
                else f"{palette.maroon}Invalid floating number input! Please try again.{RESET}"
            ),
        )

    def prompt(self) -> float | None:

        prompt = super().prompt()

        if prompt is None and self.allow_none:
            return None

        return float(prompt)
