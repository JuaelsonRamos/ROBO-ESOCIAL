from __future__ import annotations

from src.gui.views.CertificateManager import CertificateManager
from src.gui.views.SheetProcess import SheetProcess
from src.gui.widgets import ViewNavigator
from src.gui.widgets.StatusBar import ProgressCounter, StatusBar

import tkinter as tk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.anchor(tk.W)
        self.geometry('1280x720')
        self.title('ROBO-ESOCIAL')
        self.create_widgets()
        self.propagate(tk.FALSE)

    def create_widgets(self):
        # Adicionar primeiro para que as dimensões tenham precedência sob as outras
        status_bar = StatusBar(self)
        ProgressCounter(
            status_bar,
            idle='Aguardando Processamento',
            template='Processando Planilhas ({current}/{total})',
        )
        view_nav = ViewNavigator(self)
        view_nav.add_button('Certificados', CertificateManager(self))
        active = view_nav.add_button('Processar', SheetProcess(self))
        active.click()
        view_nav.add_button('Histórico')
        view_nav.add_button('Visualizar')
        view_nav.add_button('Ferramentas')
