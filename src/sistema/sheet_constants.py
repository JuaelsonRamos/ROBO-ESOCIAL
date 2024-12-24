from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence, TypeAlias

from openpyxl.styles.alignment import Alignment as _Alignment
from openpyxl.styles.colors import (
    COLOR_INDEX,
    Color as _Color,
)
from openpyxl.styles.fonts import Font as _Font


SheetFileSuffixOptions: TypeAlias = Sequence[tuple[str, tuple[str, ...]]]


def _make_file_dialog_options(pairs: SheetFileSuffixOptions) -> SheetFileSuffixOptions:
    """
    Utility function to allow list of options to grow, since is it defined in a standard
    format.

    Also, so that it (this function) can serve as a reference to implement this
    functinality elsewhere. The idea behind this function is arguable, yes, to it may be
    removed in the future, I genuenely think it may be useful for now, so let it be
    here, it's easy to substitute it, anyways.
    """
    options = []
    for desc, suffixes in pairs:
        formatted = tuple(s.lower() for s in suffixes)
        new_desc = '{} ({})'.format(desc, ';'.join(formatted))
        options.append((new_desc, suffixes))
    return tuple(options)


SHEET_FILETYPE_ASSOCIATIONS: Final[SheetFileSuffixOptions] = (
    # NOTE: Excel 2010 can be read as .xls as well
    ('Excel 2010-presente', ('*.xlsx',)),
    # NOTE: openpyxl probably can't make anything out of macros
    ('Excel Macro 2010-presente', ('*.xlsm',)),
    # TODO: differ .xls file BIFF5, BIFF8, BIFF12
    # SEE: https://support.microsoft.com/en-us/office/file-formats-that-are-supported-in-excel-0943ff2c-6014-4e8d-aaea-b83d51d46247
    ('Excel 95-2003', ('*.xls',)),
    ('Excel XML 2003', ('*.xml',)),
    ('Planilha OpenDocument', ('*.ods',)),
    ('Arquivo CSV', ('*.csv',)),
    ('Arquivo JSON', ('*.json',)),
    ('Todos os arquivos', ('*',)),
)

SHEET_FILEDIALOG_OPTIONS: Final[SheetFileSuffixOptions] = _make_file_dialog_options(
    SHEET_FILETYPE_ASSOCIATIONS
)

DEFAULT_MODEL_CELL = 'A1'


@dataclass(frozen=True, init=False)
class Fill:
    RED = 3
    BLUE = 8
    WHITE = 2


@dataclass(frozen=True, init=False)
class Color:
    BLACK = _Color(type='rgb', rgb=COLOR_INDEX[0])
    WHITE = _Color(type='rgb', rgb=COLOR_INDEX[1])
    RED = _Color(type='rgb', rgb=COLOR_INDEX[2])
    BLUE = _Color(type='rgb', rgb=COLOR_INDEX[7])


@dataclass(frozen=True, init=False)
class Font:
    HEADER = _Font(
        color=Color.BLACK,
        bold=True,
        underline=_Font.UNDERLINE_SINGLE,
        name='Times New Roman',
        size=10,
    )
    CELL = _Font(
        color=Color.BLACK,
        name='Arial',
        size=10,
    )


@dataclass(frozen=True, init=False)
class Alignment:
    HEADER = _Alignment(vertical='bottom', horizontal='left', wrap_text=False)
    CELL = _Alignment(vertical='center', horizontal='left', wrap_text=True)
