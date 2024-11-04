from __future__ import annotations

from .Column import Column
from .ColumnMetadata import ColumnMetadata
from .Row import Row
from .RowData import RowData

import pytest

from testing import fake_sheet

import sistema.spreadsheet as sheet

from sistema.validators import Validator

from typing import Any


column_values: list[str] = [
    'voluptatem et necessitatibus',
    'veniam sed asperiores',
    'assumenda illo qui',
    'eveniet dignissimos ut',
    'odio id nulla',
]

dummy_headers: list[dict] = [
    {'text': 'voluptatem et necessitatibus', 'required': sheet.OPCIONAL},
    {'text': 'veniam sed asperiores', 'required': sheet.MAYBE},
    {'text': 'assumenda illo qui', 'required': sheet.REQUIRED},
    {'text': 'eveniet dignissimos ut', 'required': sheet.OPCIONAL},
    {'text': 'odio id nulla', 'required': sheet.MAYBE},
]


class Columns(ColumnMetadata):
    voluptatem_et_necessitatibus: Column
    veniam_sed_asperiores: Column
    assumenda_illo_qui: Column
    eveniet_dignissimos_ut: Column
    odio_id_nulla: Column


class String(Validator):
    is_regular = False
    regex = None
    qualified_type = sheet.STRING

    @classmethod
    def validate(self, value: Any) -> str:
        assert isinstance(value, str)
        v = value.strip()
        assert v != ''
        return v


class Rows(RowData):
    voluptatem_et_necessitatibus: Row[String]
    veniam_sed_asperiores: Row[String]
    assumenda_illo_qui: Row[String]
    eveniet_dignissimos_ut: Row[String]
    odio_id_nulla: Row[String]


def test_args():
    with fake_sheet(model=1, headers=dummy_headers, rows=3) as fs:
        headers = next(fs.active.iter_rows(min_row=2, max_row=2))
        cols_meta = Columns.model_validate(headers)
        rows = fs.active.iter_rows(min_row=3)
        for row in rows:
            assert Rows.model_validate((cols_meta, row))
