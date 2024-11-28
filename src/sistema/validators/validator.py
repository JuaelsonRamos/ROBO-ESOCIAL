from __future__ import annotations

import src.sistema.spreadsheet as sheet

from src.sistema.models import (
    Cell as CellModel,
    Column,
)

import string

from typing import Any, Never, TypeAlias

from openpyxl.cell import Cell
from pydantic import validate_call


DefaultDict: TypeAlias = dict[str, Any]


class ValidatorError(Exception): ...


class CellValidationError(Exception): ...


class Validator:
    def __init__(
        self, *, qualified_type: sheet.QualifiedType, is_arbitrary_string: bool
    ) -> None:
        self._qualified_type = qualified_type
        self._is_arbitrary_string = is_arbitrary_string

    @property
    def qualified_type(self) -> sheet.QualifiedType:
        return self._qualified_type

    @property
    def is_arbitrary_string(self) -> bool:
        return self._is_arbitrary_string

    @validate_call
    def validate(
        self, /, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict | Never:
        if cell_index < 0:
            raise CellValidationError(f'{cell_index=} expected >= 0')
        property_name = property_name.strip(string.whitespace)
        if property_name == '':
            raise CellValidationError('property name is empty')

        return {
            'index': cell_index,
            'property_name': property_name,
            'required': column.required,
            'is_empty': False,
            'is_valid': False,
            'is_arbitrary_string': self.is_arbitrary_string,
            'qualified_type': self.qualified_type,
            'validator': self,
            'original_value': cell.value,
            'qualified_value': None,
            'column_metadata': column,
        }

    @validate_call
    def validate_model(
        self, /, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> CellModel | Never:
        namespace = self.validate(column, cell, cell_index, property_name)
        return CellModel.model_validate(namespace)
