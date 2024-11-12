from __future__ import annotations

from .exceptions import SpreadsheetObjectError

from utils import EmptyString

import string

from openpyxl.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet
from unidecode import unidecode_expect_nonascii


class SheetModel:
    def __init__(self, worksheet: Worksheet) -> None:
        self.worksheet = worksheet
        try:
            cell = self.worksheet['A1']
            assert isinstance(cell, Cell)
            name = cell.value
            assert isinstance(name, str)
            name = name.strip(string.whitespace)
            if name == '':
                raise EmptyString
            name = unidecode_expect_nonascii(name)
            assert name.isalnum()
            identifier: int | None = None
            match name:
                case 'Modelo 1':
                    identifier = 1
                case 'Modelo 2':
                    identifier = 2
                case _:
                    raise ValueError(f"modelo '{name}' é inválido")
            self._cell: Cell = cell
            self._name: str = name
            self._id: int = identifier
        except (AssertionError, ValueError, EmptyString) as err:
            raise SpreadsheetObjectError(err) from err

    @property
    def cell(self):
        return self._cell

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id
