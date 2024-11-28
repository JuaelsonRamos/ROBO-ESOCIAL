from __future__ import annotations

from .numeric_string import NumericString
from .validator import DefaultDict

import src.sistema.spreadsheet as sheet

from src.sistema.models.Column import Column
from src.utils import INT32

from typing import Never

from openpyxl.cell.cell import Cell
from pydantic import validate_call


class Integer(NumericString):
    def __init__(
        self,
        *,
        min_value: int | float = INT32.MIN,
        max_value: int | float = INT32.MAX,
        allow_zero: bool = True,
        allow_empty: bool = False,
    ):
        super().__init__(
            min_value=min_value,
            max_value=max_value,
            allow_zero=allow_zero,
            allow_empty=allow_empty,
        )
        self._is_arbitrary_string = False
        self._qualified_type = sheet.INT

    @validate_call
    def validate(
        self, /, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict | Never:
        namespace = super().validate(column, cell, cell_index, property_name)
        if not namespace['is_valid']:
            return namespace
        if namespace['is_valid'] and namespace['is_empty']:
            return namespace
        value = namespace['qualified_value']
        try:
            namespace['qualified_value'] = int(value)
        except (TypeError, ValueError):
            namespace['is_valid'] = False
            namespace['qualified_value'] = None

        return namespace
