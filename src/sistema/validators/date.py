from __future__ import annotations

from .string import String
from .validator import DefaultDict, ValidatorError

import src.sistema.spreadsheet as sheet

from src.sistema.models.Column import Column

from datetime import date, datetime
from typing import Never

from openpyxl.cell.cell import Cell
from pydantic import validate_call


_MIN_REASONABLE_DATE = date(1970, 1, 1)
_MAX_REASONABLE_DATE = date(2100, 12, 31)
_MIN_POSSIBLE_DATE = date(1, 1, 1)


class Date(String):
    min_possible_date = _MIN_POSSIBLE_DATE
    min_reasonable_date = _MIN_REASONABLE_DATE
    max_reasonable_date = _MAX_REASONABLE_DATE

    def __init__(
        self,
        *,
        min_date: date = _MIN_REASONABLE_DATE,
        max_date: date = _MAX_REASONABLE_DATE,
        allow_empty: bool = False,
    ):
        self._is_arbitrary_string = False
        self._qualified_type = sheet.DATE
        self.format_length: int = len('dd/mm/aaaa')
        super().__init__(
            min_string_length=self.format_length,
            max_string_length=self.format_length,
            case_sensitive=False,
            expect_unicode=False,
            allow_empty=allow_empty,
        )

        if min_date < self.min_reasonable_date:
            raise ValidatorError(
                f'{min_date=} expected more than {self.min_reasonable_date=}'
            )
        if max_date > self.max_reasonable_date:
            raise ValidatorError(
                f'{max_date=} expected less than {self.max_reasonable_date=}'
            )
        if min_date >= max_date:
            raise ValidatorError(f'expected {min_date=} to be less than {max_date=}')

        self.format = '%d/%m/%Y'
        self.min_date = min_date
        self.max_date = max_date

    @validate_call
    def validate(
        self, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict | Never:
        namespace = super().validate(column, cell, cell_index, property_name)
        if not namespace['is_valid']:
            return namespace
        if namespace['is_valid'] and namespace['is_empty']:
            return namespace
        value: str = namespace['qualified_value']
        try:
            t = datetime.strptime(value, self.format).date()
        except (TypeError, ValueError):
            t = None
        if t is not None and (self.min_date <= t <= self.max_date):
            namespace['qualified_value'] = t
        else:
            namespace['is_valid'] = False
            namespace['qualified_value'] = None

        return namespace
