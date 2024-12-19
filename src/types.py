from __future__ import annotations

from enum import StrEnum, auto


class IsRequired(StrEnum):
    REQUIRED = auto()
    OPTIONAL = auto()
    UNCERTAIN = auto()


class CellValueType(StrEnum):
    STRING = auto()
    INT = auto()
    FLOAT = auto()
    DATE = auto()
    BOOL = auto()
