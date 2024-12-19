from __future__ import annotations

from src import abc
from src.sistema.models import (
    Cell as CellModel,
    Column,
)
from src.sistema.spreadsheet import Fill
from src.types import CellValueType, IsRequired

import re
import string
import hashlib

from typing import Any, Iterable, Sequence

from openpyxl.cell.cell import Cell
from unidecode import unidecode_expect_nonascii as unidecode


def get_requirement(cell: Cell) -> IsRequired:
    if cell.fill == Fill.RED:
        return IsRequired.REQUIRED
    if cell.fill == Fill.BLUE:
        return IsRequired.UNCERTAIN
    return IsRequired.OPTIONAL


class Validator(abc.Validator):
    is_arbitraty_string: bool
    value_type: CellValueType

    re_spaces = re.compile(f'[{string.whitespace}]+')
    re_punctuation = re.compile(f'[{string.punctuation}]+')
    re_nonascii = re.compile(f'[^{string.printable}]+')

    def __init__(self, /, known_titles: Sequence[str]) -> None:
        self.title_hashes = self._hash_nonascii_string(known_titles)

    def _hash_nonascii_string(self, strings: Iterable[str]) -> Iterable[str]:
        _result = []
        for some_str in strings:
            as_ascii = unidecode(some_str)
            normalized = as_ascii.strip(string.whitespace + string.punctuation).lower()
            normalized = self.re_spaces.sub(' ', normalized)
            normalized = self.re_punctuation.sub('*', normalized)
            normalized = self.re_nonascii.sub('', normalized)
            hashed = hashlib.md5(normalized.encode()).hexdigest().upper()
            _result.append(hashed)
        return tuple(_result)

    def __setattr__(self, name: str, value: Any, /):
        raise NotImplementedError

    def to_dict(self, /, column: Column, cell: Cell, cell_index: int) -> dict[str, Any]:
        return {
            'index': cell_index,
            'required': get_requirement(cell),
            'validator': self,
            'original_value': cell.value,
            'column_metadata': column,
        }

    def to_model(self, /, column: Column, cell: Cell, cell_index: int) -> CellModel:
        return CellModel(**self.to_dict(column, cell, cell_index))


class String(Validator): ...


class LetterString(String): ...


class NumericString(String): ...


class IntegerString(NumericString): ...


class Float(NumericString): ...


class Integer(IntegerString): ...


class Date(String): ...


class Option(String): ...


class Boolean(String): ...
