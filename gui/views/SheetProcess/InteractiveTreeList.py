from __future__ import annotations

from gui.views.SheetProcess.QueueButtonRow import QueueButtonRow
from gui.views.SheetProcess.ShortTree import ShortTree
from gui.views.SheetProcess.data import Heading

import tkinter as tk
import tkinter.ttk as ttk


class InteractiveTreeList(ttk.Frame):
    def __init__(self, master, title: str, *, columns: dict[str, Heading]):
        super().__init__(master)
        self.title = title
        self.pack(fill=tk.BOTH, expand=tk.TRUE, side=tk.TOP, anchor=tk.NW)
        self.button_row = QueueButtonRow(self, self.title)
        self.tree = ShortTree(self, columns=columns)

    def add_button(self, text: str):
        return self.button_row.add_button(text)
