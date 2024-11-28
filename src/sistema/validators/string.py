from __future__ import annotations

from .validator import DefaultDict, Validator, ValidatorError

import src.sistema.spreadsheet as sheet

from src.sistema.models import Column
from src.utils import INT32

import string

from typing import Any, Never

from openpyxl.cell import Cell
from pydantic import validate_call
from unidecode import unidecode_expect_nonascii


class String(Validator):
    def __init__(
        self,
        *,
        min_string_length: int = 1,
        max_string_length: int = INT32.MAX,
        case_sensitive: bool = True,
        expect_unicode: bool = False,
        allow_empty: bool = True,
    ):
        super().__init__(qualified_type=sheet.STRING, is_arbitrary_string=True)
        self.__min_string_length = min_string_length
        self.__max_string_length = max_string_length
        self.case_sensitive = case_sensitive
        self.expect_unicode = expect_unicode
        self.allow_empty = allow_empty

    @property
    def min_string_length(self) -> int:
        return self.__min_string_length

    @min_string_length.setter
    def min_string_length(self, value: int) -> None:
        if value == 0:
            raise ValidatorError(f'{value=} exepected non-zero')
        if value < 0:
            raise ValidatorError(f'{value=} expected positive number')
        if value >= self.max_string_length:
            raise ValidatorError(
                f'{value=} expected less than {self.__max_string_length=}'
            )
        if value >= self.__min_string_length:
            return
        self.__min_string_length = value

    @property
    def max_string_length(self) -> int:
        return self.__max_string_length

    @max_string_length.setter
    def max_string_length(self, value: int) -> None:
        if value == 0:
            raise ValidatorError(f'{value=} exepected non-zero')
        if value < 0:
            raise ValidatorError(f'{value=} expected positive number')
        if value > INT32.MAX:
            raise ValidatorError(f'{value=} expected less than {INT32.MAX}')
        if value <= self.__min_string_length:
            raise ValidatorError(
                f'{value=} expected more than {self.__min_string_length=}'
            )
        if value <= self.__max_string_length:
            return
        self.__max_string_length = value

    def validate_string(self, value: Any) -> None | Never:
        if not isinstance(value, str):
            raise TypeError('value is not of type string')
        if value == '' and not self.allow_empty:
            raise ValueError('empty when being empty is not allowed')
        if len(value) < self.min_string_length:
            raise ValueError('too short')
        if len(value) > self.max_string_length:
            raise ValueError('too long')

    def parse_string(self, value: str) -> str:
        if value == '':
            return value
        if self.expect_unicode:
            value = unidecode_expect_nonascii(value)
        value = value.strip(string.whitespace)
        if not self.case_sensitive and value != '':
            value = value.upper()
        return value

    @validate_call
    def validate(
        self, /, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict | Never:
        namespace = super().validate(column, cell, cell_index, property_name)
        value = namespace['original_value']
        if not isinstance(value, str):
            namespace['is_valid'] = False
            return namespace
        value = self.parse_string(value)
        if value == '':
            namespace['is_empty'] = True
            namespace['is_valid'] = self.allow_empty
            namespace['qualified_value'] = ''
        elif len(value) < self.min_string_length or len(value) > self.max_string_length:
            namespace['is_valid'] = False
        else:
            namespace['is_valid'] = True
            namespace['qualified_value'] = value
        return namespace
