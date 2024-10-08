from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk


class ViewButton(ttk.Button):
    def __init__(self, master: ttk.Widget, text: str):
        super().__init__(
            master,
            text=text,
            style='ViewButton.TButton',
        )
        self.pack(fill=tk.X, side=tk.TOP, ipady=4)


class ViewNavigator(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style='ViewNavigator.TFrame')
        self.pack(side=tk.LEFT, anchor=tk.W, expand=tk.TRUE, fill=tk.Y)

    def add_button(self, text: str = 'Placeholder'):
        ViewButton(self, text)
