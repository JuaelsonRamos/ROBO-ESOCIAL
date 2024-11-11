from __future__ import annotations

import sistema.spreadsheet as sheet

from sistema.models import Column
from sistema.spreadsheet import Fill, string_to_property_name
from utils import EmptyString

from typing import Sequence

from openpyxl.cell import Cell


def parse_column_titles(row: Sequence[Cell]) -> tuple[Column, ...]:
    parsed = []
    for i, cell in enumerate(row):
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
                col['requirement'] = sheet.REQUIRED
            case Fill.BLUE:
                col['requirement'] = sheet.MAYBE
            case Fill.WHITE:
                col['requirement'] = sheet.OPCIONAL
            case _:
                col['requirement'] = sheet.OPCIONAL
        parsed.append(Column.model_validate(col))
    return tuple(parsed)
