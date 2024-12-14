from __future__ import annotations

from src.utils import Singleton

import os
import sys

from dataclasses import astuple, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Final, cast


# which bootstrapping procedures where already ran
_state = SimpleNamespace(dirs=False)


class AppBootstrapError(RuntimeError): ...


@dataclass(frozen=True)
class Directory(metaclass=Singleton):
    # define platform dependent fields
    APPDATA: Final[Path]

    # assign platform dependent fields
    if sys.platform == 'win32':
        APPDATA = (
            Path('__debug__', 'LocalAppData')
            if __debug__
            else Path(os.environ['LOCALAPPDATA'], 'RoboEsocial')
        )

    # platform independent fields
    CERT_STORAGE: Final[Path] = APPDATA / '_CertStorage'
    BLOBS: Final[Path] = APPDATA / '_Blobs'
    PLAYWRIGHT: Final[Path] = (
        Path('dist', 'playwright') if __debug__ else BLOBS / 'Playwright'
    )
    BACKUP: Final[Path] = APPDATA / '_Backup'
    DB_BACKUP: Final[Path] = BACKUP / 'Db'
    ASSETS: Final[Path] = Path('./assets/') if __debug__ else Path('./_Assets/')

    # owner=read,write,open ; group=read,open ; others=none
    mode: Final[int] = 0o750

    def ensure_mkdir(self) -> None:
        """Ensure directories exist or are created."""
        global _state
        if _state.dirs:
            raise AppBootstrapError('procedure (method) already executed once')
        for field in astuple(self):
            if not isinstance(field, Path):
                continue
            field.mkdir(mode=self.mode, parents=True, exist_ok=True)
        _state.dirs = True

    def is_ensured(self) -> bool:
        global _state
        return _state.dirs
