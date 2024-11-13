from __future__ import annotations

from .constants import MAYBE, OPCIONAL, REQUIRED
from .style import Fill
from .util import normalize_column_title

from sistema.models import Column
from utils import EmptyString

from collections.abc import Sequence

from openpyxl.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet


class SheetColumns(Sequence):
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
                'property_name': normalize_column_title(cell.value, is_unicode=True),
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

        for attr in (
            '__iter__',
            '__hash__',
            '__reversed__',
            '__contains__',
            '__len__',
            '__getitem__',
            'index',
            'count',
        ):
            if not hasattr(self._columns, attr):
                continue
            method = getattr(self._columns, attr)
            setattr(self, attr, method)
