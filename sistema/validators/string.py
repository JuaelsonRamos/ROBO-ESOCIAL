from __future__ import annotations

from .validator import DefaultDict, Validator, ValidatorError

import sistema.spreadsheet as sheet

from sistema.models import Column
from utils import INT32

import string

from typing import Any, Never

from openpyxl.cell import Cell
from unidecode import unidecode_expect_nonascii


class String(Validator):
    __min_string_length: int | None = None
    __max_string_length: int | None = None

    @property
    def min_string_length(self) -> int:
        if self.__min_string_length is None:
            msg = self._not_inited_var_errmsg
            raise ValidatorError(msg) from AttributeError(msg)
        return self.__min_string_length

    @min_string_length.setter
    def min_string_length(self, value: int) -> None:
        try:
            assert value != 0, 'valor não pode ser zero'
            assert value > 0, 'valor deve ser positivo'
            assert (
                value < self.max_string_length
            ), 'valor deve ser menor que o máximo atual'
        except AssertionError as err:
            raise ValidatorError(err) from ValueError(err)
        if self.__min_string_length is not None and value >= self.__min_string_length:
            return
        self.__min_string_length = value

    @property
    def max_string_length(self) -> int:
        if self.__max_string_length is None:
            msg = self._not_inited_var_errmsg
            raise ValidatorError(msg) from SyntaxError(msg)
        return self.__max_string_length

    @max_string_length.setter
    def max_string_length(self, value: int) -> None:
        try:
            assert value != 0, 'valor não pode ser zero'
            assert value <= INT32.MAX, f'valor deve ser menor ou igual a {INT32.MAX}'
            assert (
                value > self.min_string_length
            ), 'valor deve ser maior que o mínimo atual'
        except AssertionError as err:
            raise ValidatorError(err) from ValueError(err)
        if self.__max_string_length is not None and value <= self.__max_string_length:
            return
        self.__max_string_length = value

    def __init__(
        self,
        *,
        min_string_length: int = 1,
        max_string_length: int = INT32.MAX,
        case_sensitive: bool = True,
        expect_unicode: bool = False,
        allow_empty: bool = True,
    ):
        super().__init__()
        self._is_arbitrary_string = True
        self._qualified_type = sheet.STRING
        self.min_string_length = min_string_length
        self.max_string_length = max_string_length
        self.case_sensitive = case_sensitive
        self.expect_unicode = expect_unicode
        self.allow_empty = allow_empty

    def validate_string(self, value: Any) -> None | Never:
        if not isinstance(value, str):
            raise TypeError('value is not of type string')
        if value == '':
            if self.allow_empty:
                return
            else:
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

    def _validate(
        self, column: Column, cell: Cell, cell_index: int, property_name: str
    ) -> DefaultDict | Never:
        namespace = super()._validate(column, cell, cell_index, property_name)
        value = namespace['original_value']
        if not isinstance(value, str):
            namespace['is_valid'] = False
            return namespace
        value = self.parse_string(value)
        if value == '':
            namespace['is_empty'] = True
            namespace['is_valid'] = self.allow_empty
            namespace['qualified_value'] = ''
            return namespace
        try:
            assert len(value) >= self.min_string_length
            assert len(value) <= self.max_string_length
        except AssertionError:
            namespace['is_valid'] = False
        else:
            namespace['is_valid'] = True
            namespace['qualified_value'] = value

        return namespace
