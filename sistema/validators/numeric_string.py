from __future__ import annotations

from .string import String
from .validator import DefaultDict, ValidatorError

from sistema.models import Column
from utils import INT32

import math

from openpyxl.cell import Cell


class NumericString(String):
    def __init__(
        self,
        *,
        min_value: int | float = INT32.MIN,
        max_value: int | float = INT32.MAX,
        allow_zero: bool = True,
        allow_empty: bool = False,
    ):
        try:
            assert min_value != 0
            assert min_value >= INT32.MIN
            assert max_value <= INT32.MAX
            assert min_value < max_value
        except AssertionError as err:
            raise ValidatorError(err) from ValueError(err)

        super().__init__(allow_empty=allow_empty)
        self._is_arbitrary_string = False
        self.min_value = min_value
        self.max_value = max_value
        self.allow_zero = allow_zero

    def _validate(
        self, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict:
        namespace = super()._validate(column, cell, cell_index, property_name)
        if not namespace['is_valid']:
            return namespace
        if namespace['is_valid'] and namespace['is_empty']:
            return namespace
        value: str = namespace['qualified_value']
        try:
            assert value.isascii()
            numeric = float(value)
            assert not math.isnan(numeric)
            assert not math.isinf(numeric)
            if not self.allow_zero:
                assert numeric != 0
            assert numeric >= self.min_value
            assert numeric <= self.max_value
        except (AssertionError, TypeError, ValueError):
            namespace['is_valid'] = False
            namespace['qualified_value'] = None
        else:
            namespace['qualified_value'] = str(numeric)

        return namespace
