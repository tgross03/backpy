import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Set

import numpy as np
from rich.progress import track

from backpy.core.utils.exceptions import UnsupportedCompressionAlgorithmError


@dataclass
class CompressionAlgorithm:
    name: str
    extension: str
    description: str
    allows_compression_level: bool
    post_tar_algorithm: str = None

    @classmethod
    def from_name(cls, name):
        for algorithm in _compression_methods:
            if algorithm.name == name:
                return algorithm
        return None


_compression_methods = [
    CompressionAlgorithm(
        name="zip",
        extension=".zip",
        description="ZIP File",
        allows_compression_level=True,
    ),
    CompressionAlgorithm(
        name="gztar",
        extension=".tar.gz",
        description="gzip'ed tar-file",
        allows_compression_level=False,
        post_tar_algorithm="gz",
    ),
    CompressionAlgorithm(
        name="bztar",
        extension=".tar.bz2",
        description="bzip2'ed tar-file",
        allows_compression_level=False,
        post_tar_algorithm="bz2",
    ),
    CompressionAlgorithm(
        name="xztar",
        extension="tar.xz",
        description="xz'ed tar-file",
        allows_compression_level=False,
        post_tar_algorithm="xz",
    ),
]


def is_algorithm_available(name: str) -> bool:
    return CompressionAlgorithm.from_name(name) is not None


def compress(
    root_path: Path | str,
    archive_name: str,
    fmt: str,
    level: int,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    verbosity_level: int = 1,
    overwrite: bool = False,
) -> Path:

    if isinstance(root_path, str):
        root_path = Path(root_path)

    if not is_algorithm_available(fmt):
        raise UnsupportedCompressionAlgorithmError(
            f"Compression algorithm '{fmt}' is not available!"
        )

    if fmt == "zip":
        return _compress_zip(
            root_path=root_path,
            archive_name=archive_name,
            level=level,
            include=include,
            exclude=exclude,
            verbosity_level=verbosity_level,
            overwrite=overwrite,
        )

    return _compress_tar(
        root_path=root_path,
        archive_name=archive_name,
        compression_algorithm=CompressionAlgorithm.from_name(fmt),
        exclude=exclude,
        include=include,
        verbosity_level=verbosity_level,
        overwrite=overwrite,
    )


def filter_paths(
    root_path: Path | str,
    include: list[str] | None,
    exclude: list[str] | None = None,
) -> tuple[list[Path], float]:

    files: Set[Path] = (
        set() if include is not None and len(include) > 0 else set(root_path.rglob("*"))
    )

    print(files)

    if include is not None and len(include) > 0:
        for inc in include:
            files.update(root_path.rglob(inc))

    files = {f for f in files if f.is_file()}

    if exclude is None:
        exclude = []

    for ex in exclude:
        files -= set(root_path.rglob(ex))

    size = np.sum([file.stat().st_size for file in files])

    return list(files), size


def _compress_zip(
    root_path: Path,
    archive_name: str,
    level: int,
    include: list[str] | None,
    exclude: list[str] | None,
    verbosity_level: int,
    overwrite: bool = False,
) -> Path:

    target_path = root_path.absolute().parent / (archive_name + ".zip")

    if verbosity_level >= 1:
        print(f"Creating archive {target_path} ...")

    files, size = filter_paths(root_path=root_path, include=include, exclude=exclude)

    if overwrite:
        if verbosity_level > 1:
            print("Attempting to delete existing archive...")
        target_path.unlink(missing_ok=True)

    with zipfile.ZipFile(target_path, "x") as zipf:
        for file in track(
            files, description="Compressing files ", disable=verbosity_level < 1
        ):
            if verbosity_level > 1:
                print(f"Adding '{file}'")

            zipf.write(
                filename=file,
                arcname=file.relative_to(root_path),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=level,
            )

    if verbosity_level >= 1:
        compression_ratio = 1 - (target_path.stat().st_size / size)
        print(f"Finished compression to {target_path}.")
        print(
            f"File size reduced by {np.round(compression_ratio * 100, 2)} %  "
            f"({np.round(size * 1e-6, 4)} MB -> "
            f"{np.round(target_path.stat().st_size * 1e-6, 4)} MB)"
        )

    return target_path


def _compress_tar(
    root_path: Path,
    archive_name: str,
    compression_algorithm: CompressionAlgorithm,
    include: list[str] | None,
    exclude: list[str] | None,
    verbosity_level: int,
    overwrite: bool = False,
) -> Path:

    target_path = root_path.parent / (archive_name + compression_algorithm.extension)

    if verbosity_level > 1:
        print(f"Creating archive {target_path} ...")

    files, size = filter_paths(root_path=root_path, include=include, exclude=exclude)

    if overwrite:
        if verbosity_level > 1:
            print("Attempting to delete existing archive...")
        target_path.unlink(missing_ok=True)

    with tarfile.open(
        target_path, "x:" + compression_algorithm.post_tar_algorithm
    ) as tarf:
        for file in track(
            files, description="Compressing files ", disable=verbosity_level < 1
        ):
            if verbosity_level > 1:
                print(f"Adding: {file}")

            tarf.add(
                name=file,
                arcname=file.relative_to(root_path),
            )

    if verbosity_level >= 1:
        compression_ratio = 1 - (target_path.stat().st_size / size)
        print(f"Finished compression to {target_path}.")
        print(f"File size reduced by {np.round(compression_ratio * 100, 2)} %")

    return target_path


def unpack(
    archive_path: Path,
    target_path: Path | None,
    verbosity_level: int,
) -> Path:
    if target_path is None:
        target_path = archive_path.parent

    if verbosity_level >= 2:
        print(f"Unpacking archive '{archive_path}' ...")

    shutil.unpack_archive(
        filename=archive_path.absolute(), extract_dir=target_path.absolute()
    )

    return target_path
