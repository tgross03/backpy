import datetime
import shutil
from pathlib import Path

import pytest

from backpy.core.config import MissingKeyPolicy, TOMLConfiguration
from backpy.core.utils.exceptions import InvalidTOMLConfigurationError

_TRUE_DATA = {
    "int": 1,
    "float": 1.0,
    "int_list": [1, 2],
    "float_list": [1.0, 2.0],
    "string": "test",
    "date": datetime.datetime(
        2026,
        1,
        1,
        23,
        23,
        23,
        tzinfo=datetime.timezone(datetime.timedelta(seconds=3600)),
    ),
    "true_bool": True,
    "false_bool": False,
    "dict": {"a": 1.0, "b": 2.0},
}

_ALT_DATA = {
    "int": 2,
    "float": 2.0,
    "int_list": [3, 4],
    "float_list": [3.0, 4.0],
    "string": "toast",
    "date": datetime.datetime(
        2025,
        2,
        2,
        22,
        22,
        22,
        tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)),
    ),
    "true_bool": False,
    "false_bool": True,
    "dict": {"a": 3.0, "b": 4.0},
}


def equal_type_and_value(val1, val2) -> bool:
    return isinstance(val1, type(val2)) and val1 == val2


def test_invalid_load() -> None:
    with pytest.raises(InvalidTOMLConfigurationError):
        TOMLConfiguration(path="data/test.tom")


def test_create_on_load(tmp_path: Path) -> None:
    toml = TOMLConfiguration(path=tmp_path / "test.toml", create_if_not_exists=True)
    print(toml._path)
    assert toml.exists()


def test_valid_load() -> None:
    TOMLConfiguration(path="tests/core/config/data/test.toml")


def test_read(tmp_path: Path) -> None:
    shutil.copy(src="tests/core/config/data/test.toml", dst=tmp_path / "test.toml")

    toml = TOMLConfiguration(path=tmp_path / "test.toml")

    for key, value in _TRUE_DATA.items():
        assert key in toml
        assert equal_type_and_value(toml[key], value)

    assert toml["sectionA"] == _TRUE_DATA | {
        "subsectionA": _TRUE_DATA | {"subsubsectionA": _TRUE_DATA}
    }
    assert toml["sectionA.subsectionA"] == _TRUE_DATA | {"subsubsectionA": _TRUE_DATA}
    assert toml["sectionA"]["subsectionA"] == _TRUE_DATA | {
        "subsubsectionA": _TRUE_DATA
    }
    assert toml["sectionA.subsectionA.subsubsectionA"] == _TRUE_DATA
    assert toml["sectionA.subsectionA"]["subsubsectionA"] == _TRUE_DATA
    assert toml["sectionA"]["subsectionA"]["subsubsectionA"] == _TRUE_DATA
    assert toml["sectionB"] == _TRUE_DATA


def test_dump(tmp_path: Path) -> None:
    full_data = _TRUE_DATA | {
        "sectionA": _TRUE_DATA
        | {"subsectionA": _TRUE_DATA | {"subsubsectionA": _TRUE_DATA}},
        "sectionB": _TRUE_DATA,
    }

    toml = TOMLConfiguration(tmp_path / "true.toml", create_if_not_exists=True)
    toml.dump(full_data)

    del toml

    true_toml = TOMLConfiguration(tmp_path / "true.toml")
    assert full_data == true_toml.asdict()


def test_write(tmp_path: Path) -> None:
    shutil.copy(src="tests/core/config/data/test.toml", dst=tmp_path / "test.toml")

    toml = TOMLConfiguration(tmp_path / "test.toml")

    for key in [
        None,
        "sectionA",
        "sectionA.subsectionA",
        "sectionA.subsectionA.subsubsectionA",
        "sectionB",
    ]:
        for k, v in _ALT_DATA.items():
            if key is None:
                toml[k] = v
                assert toml[k] == v
            else:
                toml[f"{key}.{k}"] = v

    true_data = _TRUE_DATA | {
        "sectionA": _TRUE_DATA
        | {"subsectionA": _TRUE_DATA | {"subsubsectionA": _TRUE_DATA}},
        "sectionB": _TRUE_DATA,
    }

    full_data = _ALT_DATA | {
        "sectionA": _ALT_DATA
        | {"subsectionA": _ALT_DATA | {"subsubsectionA": _ALT_DATA}},
        "sectionB": _ALT_DATA,
    }

    toml.dump(true_data)

    toml["sectionA"] = full_data["sectionA"]
    assert toml["sectionA"] == full_data["sectionA"]

    toml.dump(true_data)

    toml["sectionB"] = full_data["sectionB"]
    assert toml["sectionB"] == full_data["sectionB"]

    toml.dump(true_data)

    toml["sectionA.subsectionA"] = full_data["sectionA"]["subsectionA"]
    assert toml["sectionA.subsectionA"] == full_data["sectionA"]["subsectionA"]

    toml.dump(true_data)

    toml["sectionA.subsectionA.subsubsectionA"] = full_data["sectionA"]["subsectionA"][
        "subsubsectionA"
    ]
    assert (
        toml["sectionA.subsectionA.subsubsectionA"]
        == full_data["sectionA"]["subsectionA"]["subsubsectionA"]
    )


def test_policies() -> None:
    toml = TOMLConfiguration(
        path="tests/core/config/data/test.toml",
        missing_key_policy=MissingKeyPolicy.ERROR,
    )

    with pytest.raises(KeyError):
        toml["x"]

    toml = TOMLConfiguration(
        path="tests/core/config/data/test.toml",
        missing_key_policy=MissingKeyPolicy.RETURN_NONE,
    )
    assert toml["x"] is None
