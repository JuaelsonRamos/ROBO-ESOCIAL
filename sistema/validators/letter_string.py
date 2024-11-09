from __future__ import annotations

from .string import String
from .validator import DefaultDict

from sistema.models import Column
from utils import INT32

from openpyxl.cell import Cell


class LetterString(String):
    def __init__(
        self,
        *,
        min_string_length: int = 1,
        max_string_length: int = INT32.MAX,
        case_sensitive: bool = False,
        expect_unicode: bool = False,
        allow_empty: bool = False,
    ):
        super().__init__(
            min_string_length=min_string_length,
            max_string_length=max_string_length,
            case_sensitive=case_sensitive,
            expect_unicode=expect_unicode,
            allow_empty=allow_empty,
        )
        self._is_arbitrary_string = False

    def _validate(
        self, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict:
        namespace = super()._validate(column, cell, cell_index, property_name)
        if not namespace['is_valid']:
            return namespace
        if namespace['is_valid'] and namespace['is_empty']:
            return namespace
        value = self.parse_string(namespace['qualified_value'])
        if value.isalpha():
            namespace['qualified_value'] = value
        else:
            namespace['is_valid'] = False

        return namespace
