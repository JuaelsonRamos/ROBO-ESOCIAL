from __future__ import annotations

from crawl.sheet.types import SpreadsheetType

from abc import ABC, abstractclassmethod, abstractmethod
from pathlib import Path
from typing import Never


class SpreadsheetFactory(ABC):
    @abstractclassmethod
    def from_file(cls, path: str | Path) -> Spreadsheet: ...

    @abstractclassmethod
    def from_bytes(cls, data: bytes) -> Spreadsheet: ...


class Spreadsheet(ABC):
    @abstractmethod
    def __init__(self, type: SpreadsheetType, input: str | Path | bytes):
        self.type: SpreadsheetType
        ...

    @abstractmethod
    def _validate_input(self) -> None | Never: ...

    @abstractmethod
    def _validate_output(self) -> None | Never: ...

    @abstractmethod
    def export_file(self, type: SpreadsheetType, path: str) -> Path: ...

    @abstractmethod
    def export_bytes(self, SpreadsheetType) -> bytes: ...
