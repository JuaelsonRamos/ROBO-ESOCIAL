from __future__ import annotations

from .string import String
from .validator import DefaultDict, ValidatorError

import sistema.spreadsheet as sheet

from sistema.models import Column

from typing import Sequence

from openpyxl.cell import Cell


class Boolean(String):
    def __init__(
        self,
        *,
        falsy: Sequence[str] = [],
        truthy: Sequence[str] = [],
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
        self._qualified_type = sheet.BOOL

        try:
            assert len(falsy) > 0
            assert len(truthy) > 0
            falsy_buffer, truthy_buffer = [], []
            falsy_delta = len(falsy)
            for i in range(len(falsy) + len(truthy)):
                value = falsy[i] if i < falsy_delta else truthy[i]
                assert isinstance(value, str)
                value = self.parse_string(value)
                assert value != ''
                self.min_string_length = self.max_string_length = len(value)
                (falsy_buffer if i < falsy_delta else truthy_buffer).append(value)
            self.falsy: frozenset[str] = frozenset(falsy_buffer)
            self.truthy: frozenset[str] = frozenset(truthy_buffer)
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
        value: str = namespace['qualified_value']
        try:
            self.validate_string(value)
            value = self.parse_string(value)
            if value in self.falsy:
                namespace['qualified_value'] = False
            elif value in self.truthy:
                namespace['qualified_value'] = True
            else:
                raise ValueError
        except (TypeError, ValueError):
            namespace['qualified_value'] = None
            namespace['is_valid'] = False

        return namespace
