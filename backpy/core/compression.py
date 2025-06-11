import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rich.progress import track


@dataclass
class CompressionAlgorithm:
    name: str
    extension: str
    description: str
    post_tar_algorithm: str = None

    @classmethod
    def from_name(cls, name):
        for algorithm in _compression_methods:
            if algorithm.name == name:
                return algorithm
        return None


_compression_methods = [
    CompressionAlgorithm("zip", ".zip", "ZIP File"),
    CompressionAlgorithm("gztar", ".tar.gz", "gzip'ed tar-file", "gz"),
    CompressionAlgorithm("bztar", ".tar.bz2", "bzip2'ed tar-file", "bz2"),
    CompressionAlgorithm("xztar", "tar.xz", "xz'ed tar-file", "xz"),
]


def is_algorithm_available(name: str) -> bool:
    return CompressionAlgorithm.from_name(name) is not None


def compress(
    root_path: Path | str,
    archive_name: str,
    fmt: str,
    level: int,
    exclude: list[str] | None = None,
    verbosity_level: int = 1,
    overwrite: bool = False,
) -> Path:

    if isinstance(root_path, str):
        root_path = Path(root_path)

    if not is_algorithm_available(fmt):
        raise NotImplementedError(f"Compression algorithm '{fmt}' is not available!")

    if fmt == "zip":
        return _compress_zip(
            root_path=root_path,
            archive_name=archive_name,
            level=level,
            exclude=exclude,
            verbosity_level=verbosity_level,
            overwrite=overwrite,
        )

    return _compress_tar(
        root_path=root_path,
        archive_name=archive_name,
        compression_algorithm=CompressionAlgorithm.from_name(fmt),
        exclude=exclude,
        verbosity_level=verbosity_level,
        overwrite=overwrite,
    )


def _filter_files(
    root_path: Path | str,
    exclude: list[str] | None = None,
) -> tuple[list[Path], float]:

    files = set(root_path.rglob("*"))
    for ex in exclude:
        files -= set(root_path.rglob(ex))

    size = np.sum([file.stat().st_size for file in files])

    return list(files), size


def _compress_zip(
    root_path: Path,
    archive_name: str,
    level: int,
    exclude: list[str] | None,
    verbosity_level: int,
    overwrite: bool = False,
) -> Path:

    target_path = root_path.parent / (archive_name + ".zip")

    if verbosity_level >= 1:
        print(f"Creating archive {target_path} ...")

    files, size = _filter_files(root_path=root_path, exclude=exclude)

    if overwrite:
        if verbosity_level > 1:
            print("Attempting to delete existing archive...")
        target_path.unlink(missing_ok=True)

    with zipfile.ZipFile(target_path, "x") as zipf:
        for file in track(
            files, description="Compressing files ", disable=verbosity_level < 1
        ):
            if verbosity_level > 1:
                print(f"Compressing file {file}")

            zipf.write(
                filename=file,
                arcname=file.relative_to(root_path),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=level,
            )

    if verbosity_level >= 1:
        compression_ratio = 1 - (target_path.stat().st_size / size)
        print(f"Finished compression to {target_path}.")
        print(f"Compressed by {np.round(compression_ratio * 100, 2)} %")

    return target_path


def _compress_tar(
    root_path: Path,
    archive_name: str,
    compression_algorithm: CompressionAlgorithm,
    exclude: list[Path] | None,
    verbosity_level: int,
    overwrite: bool = False,
) -> Path:

    target_path = root_path.parent / (archive_name + compression_algorithm.extension)

    if verbosity_level > 1:
        print(f"Creating archive {target_path} ...")

    files, size = _filter_files(root_path=root_path, exclude=exclude)

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
                print(f"Compressing file {file}")

            tarf.add(
                name=file,
                arcname=file.relative_to(root_path),
            )

    if verbosity_level >= 1:
        compression_ratio = 1 - (target_path.stat().st_size / size)
        print(f"Finished compression to {target_path}.")
        print(f"Compressed by {np.round(compression_ratio * 100, 2)} %")

    return target_path
