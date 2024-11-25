from __future__ import annotations

import sistema.spreadsheet as sheet

from sistema.models import (
    Cell as CellModel,
    Column,
)

import string

from typing import Any, TypeAlias

from openpyxl.cell import Cell


DefaultDict: TypeAlias = dict[str, Any]


class ValidatorError(Exception): ...


class CellValidationError(Exception): ...


class Validator:
    _not_inited_var_errmsg = 'propriedade não deve ser acessada antes de inicializada'
    _inited_var_errmsg = 'propriedade só pode ser inicializada uma única vez'

    def __init__(self) -> None:
        self._qualified_type: sheet.QualifiedType | None = None
        self._is_arbitrary_string: bool | None = None

    @property
    def qualified_type(self) -> sheet.QualifiedType:
        if self._qualified_type is None:
            msg = self._not_inited_var_errmsg
            raise ValidatorError(msg) from AttributeError(msg)
        return self._qualified_type

    @property
    def is_arbitrary_string(self) -> bool:
        if self._is_arbitrary_string is None:
            msg = self._not_inited_var_errmsg
            raise ValidatorError(msg) from AttributeError(msg)
        return self._is_arbitrary_string

    def _validate(
        self, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict:
        try:
            assert isinstance(cell, Cell)
            assert isinstance(column, Column)
            assert isinstance(cell_index, int)
            assert isinstance(property_name, str)
            assert cell_index >= 0
            property_name = property_name.strip(string.whitespace)
            assert property_name != ''
        except AssertionError as err:
            raise CellValidationError(err) from err

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

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        namespace = self._validate(column, cell, cell_index, property_name)
        return CellModel.model_validate(namespace)
