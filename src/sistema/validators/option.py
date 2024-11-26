from __future__ import annotations

from .string import String
from .validator import DefaultDict, ValidatorError

from src.sistema.models.Cell import Column

from typing import Sequence

from openpyxl.cell import Cell


class Option(String):
    def __init__(
        self,
        *,
        options: Sequence[str] = [],
        case_sensitive: bool = False,
        expect_unicode: bool = False,
        allow_empty: bool = False,
    ):
        super().__init__(
            case_sensitive=case_sensitive,
            expect_unicode=expect_unicode,
            allow_empty=allow_empty,
        )
        self._is_arbitrary_string = False

        try:
            assert len(options) > 0
            options_buffer = []
            for value in options:
                assert isinstance(value, str)
                value = self.parse_string(value)
                assert value != ''
                self.min_string_length = self.max_string_length = len(value)
                options_buffer.append(value)
            self.options: frozenset[str] = frozenset(self.options)
        except AssertionError as err:
            raise ValidatorError(err) from ValueError(err)

    def _validate(
        self, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict:
        namespace = super()._validate(column, cell, cell_index, property_name)
        if not namespace['is_valid']:
            return namespace
        if namespace['is_valid'] and namespace['is_empty']:
            return namespace
        value: str = self.parse_string(namespace['qualified_value'])
        if value in self.options:
            namespace['qualified_value'] = value
        else:
            namespace['is_valid'] = False
            namespace['qualified_value'] = None

        return namespace
