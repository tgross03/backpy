# import bz2
# import gzip
# import lzma
# import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompressionAlgorithm:
    name: str
    extension: str
    description: str

    @classmethod
    def from_name(cls, name):
        for algorithm in _compression_methods:
            if algorithm.name == name:
                return algorithm
        return None


_compression_methods = [
    CompressionAlgorithm("zip", ".zip", "ZIP File"),
    CompressionAlgorithm("gztar", ".tar.gz", "gzip'ed tar-file"),
    CompressionAlgorithm("bztar", ".tar.bz2", "bzip2'ed tar-file"),
    CompressionAlgorithm("xztar", "tar.xz", "xz'ed tar-file"),
]


def is_algorithm_available(name: str) -> bool:
    return CompressionAlgorithm.from_name(name) is not None


def compress(root_path: Path, fmt: str, exclude: list[Path] | None = None) -> Path:
    if not is_algorithm_available(fmt):
        raise NotImplementedError(f"Compression algorithm '{fmt}' is not available!")

    if fmt == "zip":
        return _compress_zip(root_path=root_path, exclude=exclude)

    tar_path = _create_tar(root_path=root_path, exclude=exclude)

    match fmt:
        case "gztar":
            return _compress_gzip(root_path=tar_path)
        case "bztar":
            return _compress_bz2(root_path=tar_path)
        case "xztar":
            return _compress_xz(root_path=tar_path)
        case _:
            raise NotImplementedError(
                f"Compression algorithm '{fmt}' is not available!"
            )


def _compress_zip(root_path: Path, exclude: list[Path] | None = None) -> Path:
    return Path()


def _create_tar(root_path: Path, exclude: list[Path] | None = None) -> Path:
    return Path()


def _compress_gzip(root_path: Path) -> Path:
    return Path()


def _compress_xz(root_path: Path) -> Path:
    return Path()


def _compress_bz2(root_path: Path) -> Path:
    return Path()
