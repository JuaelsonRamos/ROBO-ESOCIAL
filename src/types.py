from __future__ import annotations

from src.sistema.spreadsheet import Fill

from datetime import date
from enum import StrEnum, auto
from typing import Any, Never, TypeVar

from openpyxl.cell.cell import Cell
from typing_extensions import TypeIs


class IsRequired(StrEnum):
    REQUIRED = auto()
    OPTIONAL = auto()
    UNCERTAIN = auto()

    @classmethod
    def from_cell(cls, cell: Cell) -> IsRequired:
        if cell.fill == Fill.RED:
            return IsRequired.REQUIRED
        if cell.fill == Fill.BLUE:
            return IsRequired.UNCERTAIN
        return IsRequired.OPTIONAL


class CellValueType(StrEnum):
    STRING = auto()
    INT = auto()
    FLOAT = auto()
    DATE = auto()
    BOOL = auto()

    @classmethod
    def type_class(cls, enum: CellValueType) -> type[CellValue] | Never:
        """
        Returns type class (`int`, `str`, etc) that represents enum value.

        :raises: ValueError if `enum` is not a valid member
        """
        if not isinstance(enum, cls):
            raise ValueError(f'unknown enum member {enum=}')
        if enum is cls.STRING:
            return str
        if enum is cls.INT:
            return int
        if enum is cls.FLOAT:
            return float
        if enum is cls.DATE:
            return date
        if enum is cls.BOOL:
            return bool

    @classmethod
    def is_instance(cls, value: Any) -> TypeIs[CellValue]:
        """
        Checks if arbitrary value is an instance of a type represented by this enum.

        For example: if `isinstance(value, str) is True` then `True` is returned, becuase the member
        `STRING` represents the type `str`. But if `isinstance(value, Path) is True`
        then `False` is returned, because there isn't any enum member that represents
        the type `Path`.
        """
        return isinstance(value, (str, int, float, date, bool))


CellValue = str | int | float | date | bool
T_CellValue = TypeVar('T_CellValue', str, int, float, date, bool)
