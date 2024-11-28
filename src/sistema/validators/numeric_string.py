from __future__ import annotations

from .string import String
from .validator import DefaultDict, ValidatorError

from src.sistema.models import Column
from src.utils import INT32

import math

from typing import Never

from openpyxl.cell import Cell
from pydantic import validate_call


class NumericString(String):
    @validate_call
    def __init__(
        self,
        *,
        min_value: int | float = INT32.MIN,
        max_value: int | float = INT32.MAX,
        allow_zero: bool = True,
        allow_empty: bool = False,
    ):
        if min_value == 0:
            raise ValidatorError(f'{min_value=} expected non-zero')
        if max_value == 0:
            raise ValidatorError(f'{max_value=} expected non-zero')
        if min_value < INT32.MIN:
            raise ValidatorError(f'{min_value=} expected more than {INT32.MIN}')
        if max_value > INT32.MAX:
            raise ValidatorError(f'{max_value=} expected less than {INT32.MAX}')
        if min_value >= max_value:
            raise ValidatorError(f'expected {min_value=} to be less than {max_value=}')

        super().__init__(allow_empty=allow_empty)
        self._is_arbitrary_string = False
        self.min_value = min_value
        self.max_value = max_value
        self.allow_zero = allow_zero

    def validate(
        self, /, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict | Never:
        namespace = super().validate(column, cell, cell_index, property_name)
        if not namespace['is_valid']:
            return namespace
        if namespace['is_valid'] and namespace['is_empty']:
            return namespace
        value: str = namespace['qualified_value']
        numeric: float | None = None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            pass
        if (
            numeric is None
            or math.isnan(numeric)
            or math.isinf(numeric)
            or (self.allow_zero is False and numeric == 0)
            or numeric < self.min_value
            or numeric > self.max_value
        ):
            namespace['is_valid'] = False
            namespace['qualified_value'] = None
        else:
            namespace['qualified_value'] = str(numeric)

        return namespace
