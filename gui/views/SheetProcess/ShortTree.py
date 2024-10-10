from __future__ import annotations

import gui.constants as const

from gui.views.SheetProcess.data import Heading

import tkinter as tk
import tkinter.ttk as ttk


class ShortTree(ttk.Treeview):
    min_height = 10
    """Altura mínima em células."""

    def __init__(self, master, *, columns: dict[str, Heading]):
        self._columns_order = []
        for col_id, col in columns.items():
            self._columns_order.insert(col['index'], col_id)

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

        for col_id, col in columns.items():
            self.heading(col_id, text=col['text'], anchor=col['anchor'])
            self.column(
                col_id,
                stretch=tk.FALSE,
                minwidth=col['minwidth'],
                width=col['minwidth'],
            )

        # empty = ['' for _ in range(self.min_height)]
        # for i in range(self.min_height):
        #     self.insert('', i, values=empty.copy())
