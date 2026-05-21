# import shutil
import subprocess
from pathlib import Path

# import numpy as np
# import pandas as pd
# import pytest

_DATA_URL = "https://github.com/datacharmer/test_db/releases/download/v1.0.7/test_db-1.0.7.tar.gz"


def setup_database(tmp_path: Path):

    try:
        subprocess.run(f"wget {_DATA_URL}", check=True, cwd=str(tmp_path), shell=True)
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                f"curl {_DATA_URL} > {_DATA_URL.split('/')[-1]}",
                check=True,
                cwd=str(tmp_path),
                shell=True,
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "Neither wget, nor curl were found. Install either of them before using this test!"
            )

    archive_path = tmp_path / _DATA_URL.split("/")[-1]

    subprocess.run(
        f"tar -xzf {archive_path.name}", check=True, shell=True, cwd=str(tmp_path)
    )
    archive_path.unlink()

    return tmp_path / _DATA_URL.split("/")[-1].removesuffix(".tar.gz")
