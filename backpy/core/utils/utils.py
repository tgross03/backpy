from hashlib import file_digest
from pathlib import Path

import numpy as np

_unit_prefix = ["", "k", "M", "G", "T", "P", "E"]


def format_bytes(byte: int) -> str:
    if byte == 0:
        return "0 B"
    closest_base = np.floor(np.log10(byte))
    prefix = _unit_prefix[np.max([int(closest_base // 3), 0])]
    return f"{byte * 10**(-(closest_base - closest_base % 3))} {prefix}B"


def calculate_sha256sum(path: Path) -> str:
    with open(str(path), "rb") as f:
        digest = file_digest(f, "sha256")
    return digest.hexdigest()
