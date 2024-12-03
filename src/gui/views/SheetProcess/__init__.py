from __future__ import annotations

__all__ = ['SheetProcess']

from src.gui.views.View import View

import src.gui.constants as const

from src.gui.views.SheetProcess.HistoryList import HistoryList
from src.gui.views.SheetProcess.ProcessingQueue import ProcessingQueue

import tkinter as tk
import tkinter.ttk as ttk


class SheetProcess(View):
    def __init__(self, master):
        super().__init__(master, style=const.VIEW)
        self.create_widgets()

    def create_widgets(self):
        ProcessingQueue(self)
        HistoryList(self)
