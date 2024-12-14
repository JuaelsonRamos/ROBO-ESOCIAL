from __future__ import annotations

from src import bootstrap

import hashlib
import sqlite3

from pathlib import Path
from typing import Final


_dir = bootstrap.Directory()

DB_FILE: Final[Path] = _dir.APPDATA / '_app_state.db'
BACKUP_DIR: Final[Path] = _dir.DB_BACKUP

_backup_files: dict[int, Path] = {}
_backup_files_populated: bool = False


def populate_backup_files() -> None:
    """
    Go through backup directory and registers file paths for existent backup files in
    memory.

    If memory has alredy been populated, does nothing and returns None.
    """
    global _backup_files, _backup_files_populated
    if _backup_files_populated or len(_backup_files) > 0:
        return
    for p in BACKUP_DIR.iterdir():
        if p.suffix != '.db':
            continue
        try:
            i = int(p.stem[:3])
            if i in _backup_files:
                continue
            _backup_files[i] = p
        except (ValueError, TypeError):
            raise RuntimeError(f'file={str(p)} has invalid name format')
    _backup_files_populated = True


def generate_unused_backupfile_path() -> Path:
    """Generate Path objects pointing to files that don't exist yet/anymore inside the
    designed backup location.
    """
    global _backup_files, _backup_files_populated
    i: int = len(_backup_files)

    def make_path() -> Path:
        global _backup_files, BACKUP_DIR
        index: str = str(i)
        hash = hashlib.md5(index.encode()).hexdigest().upper()
        filename = f'{index.ljust(3, "0")}-{hash}.db'
        return BACKUP_DIR / filename

    if not _backup_files_populated:
        populate_backup_files()
    if _backup_files_populated and len(_backup_files) == 0:
        path = make_path()
        _backup_files[i] = path
        return path

    # ordered (shouldn't matter)
    for p in _backup_files.values():
        # windows will complain about file and dir having the same name, on top of them
        # case insensitive, which doesn't happen on posix where file != dir always and
        # names are always case sensitive
        # NOTE: on posix shell: 'path/to/thing' yields file IF AND ONLY IF it exists,
        # while 'path/to/thing/' (separator suffix) yields dir ALWAYS, and errors if it
        # doesn't exist. That is by design
        if not p.exists():
            # if path is registered as being already generated once, but file doesn't
            # exist anymore, return it, since it should not conflict with any existing
            # valid backup (file with valid name format inside specific directory)
            return p
    path = make_path()
    _backup_files[i] = path
    return path


_connections: tuple[sqlite3.Connection, ...] = ()


class ClientConfig:
    """
    Constants used to configure the database at runtime, mostly immediately upon connection.

    Doc references:
    * `.setlimit() arguments <setlimit>`_
    * `Designed default limits <defaultlimits>`_

    .. _setlimit: https://www.sqlite.org/c3ref/c_limit_attached.html
    .. _defaultlimits: https://www.sqlite.org/limits.html
    """

    # From sqlite3 docs:
    # > SQLITE_LIMIT_LENGTH
    # >     The maximum size of any string or BLOB or table row, in bytes.
    _sizeof_64KiB = 1 * 1024 * 64  # kibibytes, meaning power of 1024
    SQLITE_LIMIT_LENGTH: Final[int] = _sizeof_64KiB
    """Size limit of `TEXT` and `BLOB` types in bytes."""


def define_connection(filepath: Path | None = None) -> sqlite3.Connection:
    """Create and configure sqlite3 connection."""
    global DB_FILE
    conn = sqlite3.connect(filepath or DB_FILE)

    conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, ClientConfig.SQLITE_LIMIT_LENGTH)

    return conn


def register_connection_object(conn: sqlite3.Connection) -> None:
    """Prevent connection from being collected."""
    global _connections
    _connections = _connections + (conn,)


def toss_connection_object(conn: sqlite3.Connection) -> None:
    """Remove persistent reference to connection object, enabling it to be collected."""
    global _connections
    _connections = tuple(
        _stored_conn for _stored_conn in _connections if _stored_conn != conn
    )


def get_connection_objects() -> tuple[sqlite3.Connection, ...]:
    """Get tuple of connection instances."""
    global _connections
    return _connections
