from __future__ import annotations

from gui.widgets import ViewNavigator

import tkinter as tk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.anchor = tk.W
        self.geometry('1280x720')
        self.title('ROBO-ESOCIAL')
        self.create_widgets()

    def create_widgets(self):
        view_nav = ViewNavigator(self)
        view_nav.add_button('Certificados')
        view_nav.add_button('Processar')
        view_nav.add_button('Histórico')
        view_nav.add_button('Visualizar')
        view_nav.add_button('Ferramentas')
