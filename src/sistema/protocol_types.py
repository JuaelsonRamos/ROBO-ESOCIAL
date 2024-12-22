from __future__ import annotations

from src.types import CellValue, CellValueType, EmptyValueType

from dataclasses import Field
from pathlib import Path
from typing import Any, Generator, Never, Protocol, runtime_checkable

from openpyxl import Workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema
from typing_extensions import TypeIs


@runtime_checkable
class ModelProtocol(Protocol):
    @classmethod
    def type_adapter(cls) -> TypeAdapter: ...

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type, handler: GetCoreSchemaHandler
    ) -> CoreSchema: ...

    def astuple(self) -> tuple[Any, ...]: ...

    def asdict(self) -> dict[str, Any]: ...

    def replace(self, /, **changes: Any) -> ModelProtocol: ...

    def fields(self) -> tuple[Field[Any], ...]: ...


@runtime_checkable
class SheetProtocol(Protocol):
    workbook: Workbook
    worksheet: Worksheet
    sheet_title: str
    columns: int
    rows: int
    dimensions: tuple[str, str]
    path: Path
    st_size: int
    st_created: float
    st_modified: float
    model_cell: Cell
    model_code: int
    model_name: str
    file_type_suffix: str
    file_type_description: str

    EmptyString: EmptyValueType

    def __init__(self, path: str | Path) -> None: ...

    def as_bytes(self) -> bytes: ...

    @classmethod
    def normalize_column_title(cls, value: str) -> str | EmptyValueType: ...

    @classmethod
    def is_empty_string(cls, value: Any) -> TypeIs[EmptyValueType]: ...

    def cell_exists(self, row: int, column: int) -> bool: ...

    def row_exists(self, index: int) -> bool: ...

    def column_exists(self, index: int) -> bool: ...

    def cell(self, row: int, column: int) -> Cell | Never: ...

    def row(self, index: int) -> tuple[Cell, ...] | Never: ...

    def column(self, index: int) -> tuple[Cell, ...] | Never: ...

    def iter_rows(self) -> Generator[tuple[Cell, ...], None, None]: ...

    def iter_columns(self) -> Generator[tuple[Cell, ...], None, None]: ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    _hash: int
    _meta_hash: int
    _can_call: bool
    _can_create_new: bool
    _can_initialize: bool
    is_arbitraty_string: bool
    cell_value_type: CellValueType
    value_type: type[CellValue]
    known_titles: tuple[str, ...]
    hashed_known_titles: tuple[str, ...]
    allow_empty: bool
    column: ModelProtocol
    cell: Cell
    cell_index: int
    EmptyValue: EmptyValueType

    @classmethod
    def is_empty(cls, value: Any) -> TypeIs[EmptyValueType]: ...

    @staticmethod
    def hash_column_title(title: str) -> str: ...

    @classmethod
    def new(cls) -> ValidatorProtocol: ...

    def __new__(cls) -> ValidatorProtocol | Never: ...

    def with_data(self) -> ValidatorProtocol: ...

    def __init__(self) -> None: ...

    def __call__(self) -> Any | Never: ...

    def parse_value(self) -> CellValue | EmptyValueType | Never: ...

    def is_value_valid(self) -> bool: ...

    def to_dict(self) -> dict[str, Any]: ...

    def to_model(self) -> ModelProtocol: ...

    @classmethod
    def meta_hash(cls) -> int: ...

    @classmethod
    def __hash__(cls) -> int: ...
