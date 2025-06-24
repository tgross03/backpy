from hashlib import file_digest
from pathlib import Path


def _calculate_sha256sum(path: Path) -> str:
    with open(str(path), "rb") as f:
        digest = file_digest(f, "sha256")
    return digest.hexdigest()
