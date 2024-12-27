from __future__ import annotations

import src.sistema.validator as validator

from src.exc import SheetCell, SheetParsing, ValidatorException
from src.sistema.sheet_constants import Fill

import types
import string
import datetime

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, auto
from typing import Any, Never, TypeAlias, TypeVar, TypedDict

import numpy

from openpyxl.cell.cell import Cell
from openpyxl.cell.rich_text import CellRichText
from typing_extensions import TypeIs
from unidecode import unidecode_expect_nonascii as unidecode


class IsRequired(StrEnum):
    REQUIRED = auto()
    OPTIONAL = auto()
    UNCERTAIN = auto()

    @classmethod
    def _get_enum(cls, value: Cell | int) -> IsRequired:
        code: int = value if isinstance(value, int) else value.fill  # type: ignore
        if code == Fill.RED:
            return IsRequired.REQUIRED
        if code == Fill.BLUE:
            return IsRequired.UNCERTAIN
        return IsRequired.OPTIONAL

    @classmethod
    def _to_code(cls, value: IsRequired) -> int:
        if value is cls.REQUIRED:
            return Fill.RED
        if value is cls.UNCERTAIN:
            return Fill.BLUE
        return Fill.WHITE

    @classmethod
    def from_cell(cls, cell: Cell):
        return cls._get_enum(cell)

    @classmethod
    def from_fill_code(cls, fill: int) -> IsRequired:
        return cls._get_enum(fill)

    @classmethod
    def get_fill_code(cls, enum: IsRequired) -> int:
        return cls._to_code(enum)

    def to_fill_code(self) -> int:
        return self._to_code(self)


class SheetModel(StrEnum):
    MODELO_1 = auto()
    MODELO_2 = auto()

    @classmethod
    def enum_from_cell(cls, cell: Cell) -> SheetModel | Never:
        try:
            cell_value = validator.cell_value_to_string(cell.value)
        except ValidatorException.RuntimeError as err:
            raise SheetParsing.TypeError(err) from err
        cell_value = unidecode(cell_value).strip(string.whitespace).lower()
        if cell_value == '':
            empty_base_err = SheetCell.ValueError(
                'cell containing sheet model description is empty'
            )
            raise SheetParsing.EmptyString(empty_base_err) from empty_base_err
        model_spec: tuple[str, ...] = tuple(cell_value.split(' '))
        if len(model_spec) != 2:
            raise SheetParsing.ValueError(f'cannot infer model code by {cell_value=}')
        match model_spec:
            case ('modelo', '1'):
                return cls.MODELO_1
            case ('modelo', '2'):
                return cls.MODELO_2
        raise SheetParsing.ValueError(
            f"canont infer worksheet's model by cell {cell.coordinate=}"
        )

    @classmethod
    def code_from_cell(cls, cell: Cell) -> int:
        enum = cls.enum_from_cell(cell)
        return 1 if enum == cls.MODELO_1 else 2

    @classmethod
    def name_from_cell(cls, cell: Cell) -> str:
        enum = cls.enum_from_cell(cell)
        return 'Modelo 1' if enum == cls.MODELO_1 else 'Modelo 2'


class BrowserType(StrEnum):
    FIREFOX = auto()
    CHROMIUM = auto()

    def playwright_name(self) -> str:
        if self == self.FIREFOX:
            return 'firefox'
        if self == self.CHROMIUM:
            return 'chromium'
        raise RuntimeError('should be unreachable')

    @classmethod
    def enum_from_name(cls, name: str) -> BrowserType:
        if name == 'firefox':
            return cls.FIREFOX
        if name == 'chromium':
            return cls.CHROMIUM
        raise RuntimeError('should be unreachable')


class CellValueType(StrEnum):
    STRING = auto()
    INT = auto()
    FLOAT = auto()
    DATE = auto()
    BOOL = auto()
    DATETIME = auto()
    TIMEDELTA = auto()
    TIME = auto()

    @classmethod
    def get_type_class(cls, enum: CellValueType) -> type[CellValue] | Never:
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
            return datetime.date
        if enum is cls.BOOL:
            return bool
        if enum is cls.DATETIME:
            return datetime.datetime
        if enum is cls.TIMEDELTA:
            return datetime.timedelta
        if enum is cls.TIME:
            return datetime.time

    def as_type_class(self) -> type[CellValue]:
        return self.get_type_class(self)

    @classmethod
    def is_instance(cls, value: Any) -> TypeIs[CellValue]:
        """
        Checks if arbitrary value is an instance of a type represented by this enum.

        For example: if `isinstance(value, str) is True` then `True` is returned, becuase the member
        `STRING` represents the type `str`. But if `isinstance(value, Path) is True`
        then `False` is returned, because there isn't any enum member that represents
        the type `Path`.
        """
        return isinstance(
            value,
            (
                str,
                int,
                float,
                datetime.date,
                datetime.datetime,
                datetime.time,
                datetime.timedelta,
                bool,
            ),
        )


CellValue = (
    str
    | int
    | float
    | datetime.date
    | datetime.datetime
    | datetime.time
    | datetime.timedelta
    | bool
)
T_CellValue = TypeVar(
    'T_CellValue',
    str,
    int,
    float,
    datetime.date,
    datetime.datetime,
    datetime.time,
    datetime.timedelta,
    bool,
)


class EmptyValueType(object): ...


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


class TaskInitState(TypedDict):
    workbook_db_id: int
    certificate_db_id: int
