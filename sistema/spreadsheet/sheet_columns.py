from __future__ import annotations

from .constants import MAYBE, OPCIONAL, REQUIRED
from .style import Fill
from .util import string_to_property_name

from sistema.models import Column
from utils import EmptyString

from typing import Any

from openpyxl.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet


class SheetColumns:
    def __init__(self, worksheet: Worksheet) -> None:
        self.worksheet = worksheet
        self.row: tuple[Cell, ...]
        self.row = next(self.worksheet.iter_rows(min_row=2, max_row=2))
        parsed = []
        for i, cell in enumerate(self.row):
            if not isinstance(cell, Cell):
                raise TypeError('must be spreadsheet Cell object')
            if not isinstance(cell.value, str):
                raise TypeError('must be string object')
            if cell.value == '':
                raise EmptyString
            col = {
                'index': i,
                'original_text': cell.value,
                'property_name': string_to_property_name(cell.value, is_unicode=True),
            }
            match cell.fill:
                case Fill.RED:
                    col['requirement'] = REQUIRED
                case Fill.BLUE:
                    col['requirement'] = MAYBE
                case Fill.WHITE:
                    col['requirement'] = OPCIONAL
                case _:
                    col['requirement'] = OPCIONAL
            parsed.append(Column(**col))
        self._columns = tuple(parsed)

    def __iter__(self):
        return self._columns.__iter__()

    def __hash__(self) -> int:
        return self._columns.__hash__()

    def __reversed__(self):
        return self._columns.__reversed__()

    def __contains__(self, value: Any):
        return self._columns.__contains__(value)

    def __len__(self):
        return self._columns.__len__()

    def __getitem__(self, index: int):
        return self._columns.__getitem__(index)
