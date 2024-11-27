from __future__ import annotations

import src.gui.constants as const

from src.gui.views.SheetProcess.data import HeadingSequence
from src.utils import extract_from

import tkinter as tk
import tkinter.ttk as ttk


class ShortTree(ttk.Treeview):
    min_height = 10
    """Altura mínima em células."""

    def __init__(self, master: ttk.Widget, *, columns: HeadingSequence):
        self.columns = columns
        self._columns_order = tuple(col['iid'] for col in columns)

        super().__init__(
            master,
            style=const.SHORT_TREE,
            height=self.min_height,
            selectmode=tk.EXTENDED,
            takefocus=tk.TRUE,
            columns=self._columns_order,
            show='headings',
        )
        self.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)

        for col in columns:
            self.heading(col['iid'], **extract_from(col, 'text', 'anchor'))
            self.column(
                col['iid'],
                stretch=tk.FALSE,
                **extract_from(col, 'width', 'minwidth'),
            )

        # empty = ['' for _ in range(self.min_height)]
        # for i in range(self.min_height):
        #     self.insert('', i, values=empty.copy())
