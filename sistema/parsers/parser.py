from __future__ import annotations

from sistema.models import (
    Cell as CellModel,
    Column,
)
from sistema.spreadsheet import string_to_property_name
from sistema.validators import Validator

from abc import abstractmethod
from typing import Any, Never, Sequence, cast

from openpyxl.cell import Cell


class Parser:
    _schema: dict[str, Validator] | None = None

    def __init__(self) -> None:
        self._define_schema()

    def _define_schema(self):
        if self._schema is not None:
            raise ValueError('schema deve ser inicializado apenas uma vez')

    def schema(self) -> dict[str, Validator]:
        if self._schema is None:
            raise ValueError('schema não inicializado')
        return self._schema.copy()

    def validate_row_data(
        self, columns: Sequence[Column], row: Sequence[Cell]
    ) -> None | Never:
        assert self._schema is not None, 'schema ainda não definido'
        assert len(row) > 0
        assert len(columns) > 0
        assert all(isinstance(v, Cell) for v in row)
        assert all(isinstance(v, Column) for v in columns)
        assert len(row) == len(columns)
        assert len(row) == len(self._schema)

    def parse_row(
        self, columns: Sequence[Column], row: Sequence[Cell]
    ) -> tuple[CellModel, ...]:
        self._schema = cast(dict, self._schema)
        parsed: list[Any] = [None] * len(row)
        for col in columns:
            assert col.property_name in self._schema
            validate = self._schema[col.property_name]
            cell = row[col.index]
            parsed[col.index] = validate(col, cell, col.index, col.property_name)
        parsed = cast(list[Validator], parsed)
        return tuple(parsed)

    @abstractmethod
    def parse_context(
        self, parsed_row: Sequence[CellModel]
    ) -> tuple[CellModel, ...]: ...
