from __future__ import annotations

import src.db.tables as table

from src.exc import SheetParsing
from src.types import EmptyValueType

import io
import re
import string

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Generator, Never, Sequence

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet
from typing_extensions import TypeIs
from unidecode import unidecode_expect_nonascii as unidecode


# TODO: generate column model
# TODO: validate cell


class Sheet:
    workbook: Workbook
    db_workbook: table.WorkbookDict
    worksheets: Sequence[Worksheet]
    db_worksheets: Sequence[table.WorksheetDict]
    _sheet: Worksheet | None
    columns: int
    rows: int
    dimensions: tuple[str, str]
    path: Path
    st_size: int
    st_created: float
    st_modified: float

    EmptyString: EmptyValueType = EmptyValueType()

    @property
    def sheet(self):
        return self._sheet

    @sheet.setter
    def sheet(self, another: Worksheet):
        self.columns = another.max_column
        self.rows = another.max_row
        self._sheet = another

    def get_sheet(self) -> Worksheet:
        if self._sheet is None:
            raise SheetParsing.ValueError(
                'sheet property is not set to valid worksheet'
            )
        return self._sheet

    def set_sheet(self, another: Worksheet):
        self.sheet = another

    def __init__(self, path: str | Path) -> None:
        # Load spreadsheet
        if isinstance(path, str):
            self.workbook = load_workbook(path)
            path = Path(path)
        else:
            self.workbook = load_workbook(str(path))
        self.db_workbook = table.Workbook.from_file(path)
        self.worksheets = tuple(self.workbook.worksheets)
        if len(self.worksheets) == 0:
            self.db_worksheets = ()
            self._sheet = None
        else:
            self.db_worksheets = tuple(
                table.Worksheet.from_sheet_obj(self.workbook, sheet)
                for sheet in self.worksheets
            )
            self._sheet = self.worksheets[0]
        self.path = path
        stat = self.path.stat()
        self.st_size = stat.st_size
        self.st_created = stat.st_ctime
        self.st_modified = stat.st_mtime

    def as_bytes(self) -> bytes:
        with NamedTemporaryFile() as tmp:
            self.workbook.save(tmp)
            return tmp.read()

    @classmethod
    def normalize_column_title(cls, value: str) -> str | EmptyValueType:
        value = value.strip(string.whitespace)
        if value == '':
            return cls.EmptyString
        value = unidecode(value)
        value = value.lower()
        replace = {'$': 's'}
        with io.StringIO() as property_name:
            for ch in value:
                property_name.write(replace.get(ch, ch))
            value = property_name.getvalue()
        value = re.sub(r'[^a-z0-9]+', '_', value).strip('_')
        if value == '':
            return cls.EmptyString
        return value

    @classmethod
    def is_empty_string(cls, value: Any) -> TypeIs[EmptyValueType]:
        return isinstance(value, EmptyValueType) and value is cls.EmptyString

    def cell_exists(self, row: int, column: int) -> bool:
        if row < 1 or column < 1:
            # indexes are positive and 1-based
            return False
        if (row, column) == (1, 1):
            # model metadata cell
            return True
        if row == 1 and column > 1:
            # there's only one valid cell in the first row: the very first cell
            return False
        headings: int = 2
        if row == headings and column <= self.columns:
            # column headings row
            # all cells are supposed to valid in this row
            return True
        # any other cell in the range have arbitrary values
        # if they have no value, they're deemed empty
        return headings <= row <= self.rows and 1 <= column <= self.columns

    def row_exists(self, index: int) -> bool:
        return 1 <= index <= self.rows

    def column_exists(self, index: int) -> bool:
        return 1 <= index <= self.columns

    def cell(self, row: int, column: int) -> Cell | Never:
        if not self.cell_exists(row, column):
            raise SheetParsing.IndexError(f'cell does not exist {row=} {column=}')
        return self.get_sheet().cell(row, column)

    def row(self, index: int) -> tuple[Cell, ...] | Never:
        if not self.row_exists(index):
            raise SheetParsing.ValueError(f'row {index=} does not exist')
        row = next(self.get_sheet().iter_rows(min_row=index, max_row=index))
        return row

    def column(self, index: int) -> tuple[Cell, ...] | Never:
        if not self.column_exists(index):
            raise SheetParsing.ValueError(f'column {index=} does not exist')
        col = next(self.get_sheet().iter_cols(min_col=index, max_col=index))
        return col

    def iter_rows(self) -> Generator[tuple[Cell, ...], None, None]:
        # TODO generator yields model
        headings_index: int = 2
        return self.get_sheet().iter_rows(
            min_row=headings_index + 1,
            max_row=self.rows,
            min_col=1,
            max_col=self.columns,
        )

    def iter_columns(self) -> Generator[tuple[Cell, ...], None, None]:
        # TODO generator yields model
        headings_index: int = 2
        return self.get_sheet().iter_cols(
            min_row=headings_index + 1,
            max_row=self.rows,
            min_col=1,
            max_col=self.columns,
        )
