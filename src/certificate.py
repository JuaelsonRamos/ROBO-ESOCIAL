from __future__ import annotations

from src.windows import APPDATA_DIR

import hashlib

from pathlib import Path
from typing import IO, Any, Final, Never


STORAGE_DIR: Final[Path] = APPDATA_DIR / '_cert_storage_'

if not STORAGE_DIR.exists():
    STORAGE_DIR.mkdir(mode=0o750, parents=True, exist_ok=False)

CERT_SUFFIX: Final[tuple[str, ...]] = ('.crt', '.pem', '.pfx')


class CertificateTypeError(Exception): ...


class CertificateFileError(Exception): ...


def _path(file: str | Path | IO) -> Path:
    if isinstance(file, str):
        return Path(file)
    if isinstance(file, IO):
        return Path(file.name)
    return file


def _is_path_corrupt(path: Path) -> None | Never:
    if path.exists() and not path.is_file():
        raise RuntimeError(f'CORRUPT REGISTRY: {path=} is exist but is not a file')


def _bytes_and_dest_path(path: Path) -> tuple[bytes, Path]:
    data = path.read_bytes()
    if __debug__:
        dest_path = STORAGE_DIR / path.name
    else:
        stem = hashlib.sha512(data).hexdigest()
        dest_path = STORAGE_DIR / path.with_stem(stem).name
    return data, dest_path


def ensure_bootstrap() -> None | Never:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_certificates() -> tuple[Path, ...]:
    certs = []
    for path in STORAGE_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() not in CERT_SUFFIX:
            continue
        certs.append(path)
    return tuple(certs)


def copy_certificate(
    file: str | Path | IO, can_overwrite: bool = False, /
) -> None | Never:
    path = _path(file)
    if path.suffix.lower() not in CERT_SUFFIX:
        raise CertificateTypeError(f'{path.suffix=} expected value in {CERT_SUFFIX}')
    _is_path_corrupt(path)
    data, dest_path = _bytes_and_dest_path(path)
    if dest_path.exists() and not can_overwrite:
        raise CertificateFileError(f'{path=} already exists')
    if not dest_path.exists():
        dest_path.touch(mode=0o600, exist_ok=False)
    dest_path.write_bytes(data)


def delete_certificate(file: str | Path | IO, /) -> None | Never:
    path = _path(file)
    _is_path_corrupt(path)
    _, dest_path = _bytes_and_dest_path(path)
    if not dest_path.exists():
        raise CertificateFileError(f'{path=} does not exist')
    dest_path.unlink()
