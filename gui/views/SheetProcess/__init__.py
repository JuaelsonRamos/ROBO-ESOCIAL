from __future__ import annotations


__all__ = ['SheetProcess']

import gui.constants as const

from gui.views.SheetProcess.ProcessingQueue import ProcessingQueue

import tkinter as tk
import tkinter.ttk as ttk


class SheetProcess(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style=const.VIEW)
        self.pack(fill=tk.BOTH, expand=tk.TRUE)
        self.create_widgets()

    def create_widgets(self):
        ProcessingQueue(self)
