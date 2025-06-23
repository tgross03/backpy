from collections.abc import Callable

# from fuzzyfinder import fuzzyfinder

# from backpy.cli.colors import PALETTE


def _validate_always(**kwargs) -> bool:
    return True


class Confirm:
    def __init__(self, name: str, message: str, default_value: bool) -> None:
        self.name: str = name
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

            if (
                in_value.lower() != "y"
                and in_value.lower() != "n"
                and in_value is not None
            ):
                print("")
                continue

            confirmation = (in_value) or self._get_default_input().lower() == "y"
            valid_input = True

        return confirmation


class TextInput:
    def __init__(
        self,
        name: str,
        message: str,
        default_value: str | None = None,
        validate: Callable[[str], bool] = _validate_always,
        suggest_matches: bool = False,
        suggestible_values: list[str] | None = None,
        confirm_suggestion: bool = True,
        only_suggestible: bool = True,
        highlight_suggestion: bool = True,
        validation_policy: str = "retry",
    ):
        self.name: str = name
        self.message: str = message
        self.default_value: str | None = default_value
        self._validate: Callable[[str], bool] = validate
        self.suggest_matches: bool = suggest_matches
        self.suggestible_values: list[str] = (
            [] if suggestible_values is None else suggestible_values
        )
        self.confirm_suggestion: bool = confirm_suggestion
        self.only_suggestible: bool = only_suggestible

    def _get_prompt(self) -> str:
        return f"{self.message} "

    def prompt(self) -> str:
        # value = input(self._get_prompt())

        if self.suggest_matches:
            None
        # valid_input = self._validate(value)
