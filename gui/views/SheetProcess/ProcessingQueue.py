from __future__ import annotations

import gui.views.SheetProcess.data as data

from gui.views.SheetProcess.InteractiveTreeList import InteractiveTreeList

import tkinter as tk
import tkinter.ttk as ttk


class ProcessingQueue(InteractiveTreeList):
    def __init__(self, master):
        super().__init__(
            master, 'Fila de Processamento', columns=data.input_queue.columns
        )
        self.add_button('Adicionar')
        self.add_button('Remover')
        self.add_button('Começar')
        self.add_button('Pausar')
        self.add_button('Parar')
