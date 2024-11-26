from __future__ import annotations

from src.gui.utils.units import length

import tkinter as tk
import tkinter.ttk as ttk


class StatusBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, height=length.point(16), padding=4)
        self.pack(side=tk.BOTTOM, fill=tk.X)
