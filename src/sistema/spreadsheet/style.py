from __future__ import annotations

from dataclasses import dataclass

import openpyxl.styles.colors as xl_colors
import openpyxl.styles.alignment as xl_alignment

from openpyxl.styles.fonts import Font as _Font


@dataclass(frozen=True, init=False)
class Fill:
    RED = 3
    BLUE = 8
    WHITE = 2


@dataclass(frozen=True, init=False)
class Color:
    BLACK = xl_colors.Color(type='rgb', rgb=xl_colors.COLOR_INDEX[0])
    WHITE = xl_colors.Color(type='rgb', rgb=xl_colors.COLOR_INDEX[1])
    RED = xl_colors.Color(type='rgb', rgb=xl_colors.COLOR_INDEX[2])
    BLUE = xl_colors.Color(type='rgb', rgb=xl_colors.COLOR_INDEX[7])


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
    HEADER = xl_alignment.Alignment(
        vertical='bottom', horizontal='left', wrap_text=False
    )
    CELL = xl_alignment.Alignment(vertical='center', horizontal='left', wrap_text=True)
