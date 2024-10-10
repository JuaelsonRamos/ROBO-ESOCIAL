from __future__ import annotations

import gui.views.SheetProcess.data as data

from gui.views.SheetProcess.QueueButtonRow import QueueButtonRow
from gui.views.SheetProcess.ShortTree import ShortTree

import tkinter as tk
import tkinter.ttk as ttk


class ProcessingQueue(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.X, side=tk.TOP, anchor=tk.NW)
        self.create_widgets()

    def create_widgets(self):
        button_row = QueueButtonRow(self, 'Fila de Processamento')
        button_row.add_button('Adicionar')
        button_row.add_button('Remover')
        button_row.add_button('Começar')
        button_row.add_button('Pausar')
        button_row.add_button('Parar')

        ShortTree(self, columns=data.input_queue.columns)
