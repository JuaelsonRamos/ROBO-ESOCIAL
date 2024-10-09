from __future__ import annotations

import gui.constants as const

import tkinter as tk
import tkinter.ttk as ttk


class ViewButton(ttk.Button):
    def __init__(self, master: ttk.Widget, text: str, *, index: int):
        super().__init__(master, text=text, style=const.VIEW_BUTTON, command=self.click)
        self.pack(fill=tk.X, side=tk.TOP, ipady=4)
        self.index = index

    def click(self):
        self.master.switch_view(self.index)

    def active(self):
        if self.state == const.PRESSED:
            return
        self.state = const.PRESSED
        self.config(style=const.ACTIVE_VIEW_BUTTON)

    def disabled(self):
        if self.state == const.NOTPRESSED:
            return
        self.state = const.NOTPRESSED
        self.config(style=const.VIEW_BUTTON)


class ViewNavigator(ttk.Frame):
    _buttons: list[tk.Widget] = []

    def __init__(self, master):
        super().__init__(master, style=const.VIEW_NAVIGATOR)
        self.pack(side=tk.LEFT, anchor=tk.W, expand=tk.TRUE, fill=tk.Y)

    def add_button(self, text: str = 'Placeholder'):
        self._buttons.append(ViewButton(self, text, index=len(self._buttons)))

    def switch_view(self, index: int):
        for btn in self._buttons:
            btn.active() if btn.index == index else btn.disabled()
