from __future__ import annotations

from .constants import MAYBE, OPCIONAL, REQUIRED
from .style import Fill
from .util import normalize_column_title

from src.sistema.models import Column
from src.utils import EmptyString

from typing import Self

from openpyxl.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet


class SheetColumns(tuple[Column, ...]):
    worksheet: Worksheet
    row: tuple[Cell, ...]

    def __new__(cls, worksheet: Worksheet) -> Self:
        cls.worksheet = worksheet
        cls.row = next(cls.worksheet.iter_rows(min_row=2, max_row=2))
        parsed = []
        for i, cell in enumerate(cls.row):
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
        return super(SheetColumns, cls).__new__(cls, parsed)
