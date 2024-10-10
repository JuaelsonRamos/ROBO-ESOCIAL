from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk


class QueueButton(ttk.Button):
    def __init__(self, master, text: str):
        super().__init__(master, text=text)
        # NOTE side=RIGHT orders things in reverse, instead of just justifying position
        self.pack(side=tk.RIGHT)

    def before(self, button: ttk.Widget):
        self.pack_configure(before=button)


class QueueButtonRow(ttk.Frame):
    _buttons: list[ttk.Button] = []

    def __init__(self, master):
        super().__init__(master)
        self.pack(anchor=tk.NE, side=tk.TOP, fill=tk.X)

    def add_button(self, text: str = 'Placeholder') -> ttk.Button:
        btn = QueueButton(self, text)
        if len(self._buttons) > 0:
            btn.before(self._buttons[-1])
        self._buttons.append(btn)
        return btn
