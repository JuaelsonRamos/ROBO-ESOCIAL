from __future__ import annotations

from .string import String
from .validator import DefaultDict, ValidatorError

import src.sistema.spreadsheet as sheet

from src.sistema.models import Column

from typing import Never, Sequence

from openpyxl.cell import Cell
from pydantic import validate_call


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

        if len(falsy) == 0:
            raise ValidatorError(f'{len(falsy)=}')
        if len(truthy) == 0:
            raise ValidatorError(f'{len(truthy)=}')
        if not isinstance(falsy, list):
            falsy = list(falsy)
        if not isinstance(truthy, list):
            truthy = list(truthy)
        for i in range(len(falsy) + len(truthy)):
            sequence = falsy if i < len(falsy) else truthy
            try:
                v = sequence[i]
                self.validate_string(v)
                v = self.parse_string(sequence[i])
            except (TypeError, ValueError) as err:
                raise ValidatorError(err) from err
            self.min_string_length = self.max_string_length = len(v)
            sequence[i] = v
        self.falsy = frozenset(falsy)
        self.truthy = frozenset(truthy)

    @validate_call
    def validate(
        self, /, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict | Never:
        namespace = super().validate(column, cell, cell_index, property_name)
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
