from hashlib import file_digest
from pathlib import Path

import numpy as np

_unit_prefix = {"": 0, "k": 3, "M": 6, "G": 9, "T": 12, "P": 15, "E": 18}


def bytes2str(byte: int) -> str:
    if byte == 0:
        return "0 B"
    if byte == -1:
        return "∞"
    closest_base = np.floor(np.log10(byte))
    prefix = list(_unit_prefix.keys())[np.max([int(closest_base // 3), 0])]
    return f"{np.round(byte * 10 ** (-(closest_base - closest_base % 3)), 2)} {prefix}B"


def str2bytes(string: str) -> int:
    components = string.split(" ")
    if len(components) != 2:
        raise ValueError("The given is not a valid memory size string (e.g. '1 MB')")

    num = float(components[0])
    unit_prefix = components[1].removesuffix("B")

    if unit_prefix not in _unit_prefix:
        raise ValueError(
            f"The given unit prefix is not valid! Possible values: "
            f"{list(_unit_prefix.keys())}"
        )

    return int(np.round(num * 10 ** _unit_prefix[unit_prefix]))


def calculate_sha256sum(path: Path) -> str:
    with open(str(path), "rb") as f:
        digest = file_digest(f, "sha256")
    return digest.hexdigest()
