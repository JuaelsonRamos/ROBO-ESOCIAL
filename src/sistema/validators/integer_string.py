from __future__ import annotations

from .numeric_string import NumericString

from src.sistema.models.Column import Column
from src.sistema.validators.validator import DefaultDict

from openpyxl.cell.cell import Cell


class IntegerString(NumericString):
    def _validate(
        self, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict:
        namespace = super()._validate(column, cell, cell_index, property_name)
        if not namespace['is_valid']:
            return namespace
        if namespace['is_valid'] and namespace['is_empty']:
            return namespace
        if not namespace['qualified_value'].isdigit():
            namespace['is_valid'] = False
            namespace['qualified_value'] = None

        return namespace
