from __future__ import annotations

import src.sistema.validator as validator

from src.exc import SheetCell, SheetParsing, ValidatorException
from src.sistema.sheet_constants import SHEET_FILETYPE_ASSOCIATIONS
from src.types import EmptyValueType

import io
import re
import string

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Generator, Never

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet
from typing_extensions import TypeIs
from unidecode import unidecode_expect_nonascii as unidecode


class Sheet:
    workbook: Workbook
    worksheet: Worksheet
    sheet_title: str
    columns: int
    rows: int
    dimensions: tuple[str, str]
    path: Path
    st_size: int
    st_created: float
    st_modified: float
    model_cell: Cell
    model_code: int
    model_name: str
    file_type_suffix: str
    file_type_description: str

    EmptyString: EmptyValueType = EmptyValueType()

    def __init__(self, path: str | Path) -> None:
        # Load spreadsheet
        if isinstance(path, str):
            self.workbook = load_workbook(path)
            path = Path(path)
        else:
            self.workbook = load_workbook(str(path))
        sheet = self.workbook.active
        if sheet is None:
            raise ValueError(
                'path successfully parsed as workbook but it contains no worksheet'
            )
        self.worksheet = sheet
        self.sheet_title = self.worksheet.title

        # Spreadsheet file's useful filesystem metadata
        self.path = path
        stat = self.path.stat()
        self.st_size = stat.st_size
        self.st_created = stat.st_ctime
        self.st_modified = stat.st_mtime

        # Get model code (number)
        self.model_cell = self.worksheet['A1']
        cell_value: str = ''
        try:
            cell_value = validator.String.cell_value_to_string(self.model_cell.value)
        except ValidatorException.RuntimeError as err:
            raise SheetParsing.TypeError(err) from err
        cell_value = unidecode(cell_value).strip(string.whitespace).lower()
        if cell_value == '':
            empty_base_err = SheetCell.ValueError(
                'cell containing sheet model description is empty'
            )
            raise SheetParsing.EmptyString(empty_base_err) from empty_base_err
        model_spec: list[str] = cell_value.split(' ')
        if len(model_spec) != 2:
            raise SheetParsing.ValueError(f'cannot infer model code by {cell_value=}')
        match model_spec:
            case ('modelo', '1'):
                self.model = 1
                self.model_name = 'Modelo 1'
            case ('modelo', '2'):
                self.model = 2
                self.model_name = 'Modelo 2'
            case _:
                raise SheetParsing.ValueError(
                    f'unknown cell value prevents inference of model code {cell_value=}'
                )

        # Spreadsheet useful metadata
        self.columns = self.worksheet.max_column
        self.rows = self.worksheet.max_row
        dimensions = self.worksheet.calculate_dimension()
        if dimensions == '' or ':' not in dimensions:
            self.dimensions = ('', '')
        else:
            self.dimensions = tuple(dimensions.split(':'))  # type: ignore

        # Spreadsheet's file type metadata
        self.file_type_description = ''
        self.file_type_suffix = ''
        for desc, suffixes in SHEET_FILETYPE_ASSOCIATIONS:
            normal_self_suffix = self.path.suffix.strip(string.punctuation).lower()
            normalized_suffixes = [
                s.strip(string.punctuation).lower() for s in suffixes
            ]
            if normal_self_suffix not in normalized_suffixes:
                continue
            self.file_type_description = desc.strip(string.whitespace)
            self.file_type_suffix = normal_self_suffix
            break

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
        return self.worksheet.cell(row, column)

    def row(self, index: int) -> tuple[Cell, ...] | Never:
        if not self.row_exists(index):
            raise SheetParsing.ValueError(f'row {index=} does not exist')
        row = next(self.worksheet.iter_rows(min_row=index, max_row=index))
        return row

    def column(self, index: int) -> tuple[Cell, ...] | Never:
        if not self.column_exists(index):
            raise SheetParsing.ValueError(f'column {index=} does not exist')
        col = next(self.worksheet.iter_cols(min_col=index, max_col=index))
        return col

    def iter_rows(self) -> Generator[tuple[Cell, ...], None, None]:
        # TODO generator yields model
        headings_index: int = 2
        return self.worksheet.iter_rows(
            min_row=headings_index + 1,
            max_row=self.rows,
            min_col=1,
            max_col=self.columns,
        )

    def iter_columns(self) -> Generator[tuple[Cell, ...], None, None]:
        # TODO generator yields model
        headings_index: int = 2
        return self.worksheet.iter_cols(
            min_row=headings_index + 1,
            max_row=self.rows,
            min_col=1,
            max_col=self.columns,
        )
