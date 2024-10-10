from __future__ import annotations

from gui.views.SheetProcess import SheetProcess
from gui.widgets import ProcessingSheetsCounter, StatusBar, ViewNavigator

import tkinter as tk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.anchor = tk.W
        self.geometry('1280x720')
        self.title('ROBO-ESOCIAL')
        self.create_widgets()
        self.propagate(tk.FALSE)

    def create_widgets(self):
        # Adicionar primeiro para que as dimensões tenham precedência sob as outras
        status_bar = StatusBar(self)
        ProcessingSheetsCounter(status_bar)
        view_nav = ViewNavigator(self)
        view_nav.add_button('Certificados')
        view_nav.add_button('Processar', active=True)
        view_nav.add_button('Histórico')
        view_nav.add_button('Visualizar')
        view_nav.add_button('Ferramentas')
        SheetProcess(self)
