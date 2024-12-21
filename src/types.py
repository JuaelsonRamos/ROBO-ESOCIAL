from __future__ import annotations

from src.sistema.spreadsheet import Fill

import types
import datetime

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum, auto
from typing import Any, Never, TypeAlias, TypeVar

import numpy

from openpyxl.cell.cell import Cell
from openpyxl.cell.rich_text import CellRichText
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

NumpyNumeric = (
    numpy.short
    | numpy.ushort
    | numpy.intc
    | numpy.uintc
    | numpy.int_
    | numpy.uint
    | numpy.longlong
    | numpy.ulonglong
    | numpy.half
    | numpy.float16
    | numpy.single
    | numpy.double
    | numpy.longdouble
    | numpy.int8
    | numpy.int16
    | numpy.int32
    | numpy.int64
    | numpy.uint8
    | numpy.uint16
    | numpy.uint32
    | numpy.uint64
    | numpy.intp
    | numpy.uintp
    | numpy.float32
    | numpy.float64
    | numpy.bool_
    | numpy.floating
    | numpy.integer
)


@dataclass(frozen=True, init=False, slots=True)
class OpenpyxlCell:
    NumpyNumeric = NumpyNumeric
    Numeric = int | float | Decimal
    Time = datetime.datetime | datetime.date | datetime.time | datetime.timedelta
    String = str | bytes | CellRichText
    Boolean: TypeAlias = bool
    NoneType: TypeAlias = types.NoneType
    KnownTypes = NumpyNumeric | Numeric | Time | String | Boolean | NoneType
