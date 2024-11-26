from __future__ import annotations

import src.gui.constants as const

import tkinter as tk
import tkinter.ttk as ttk


class ViewButton(ttk.Button):
    def __init__(self, master: ViewNavigator, text: str, *, index: int):
        super().__init__(master, text=text, style=const.VIEW_BUTTON, command=self.click)
        self.pack(fill=tk.X, side=tk.TOP, ipady=4)
        self.index = index

    def click(self):
        self.master.event_generate('<<SwitchView>>', state=self.index)

    def active(self):
        if self.instate([const.PRESSED]):
            return
        self.state([const.PRESSED])
        self.config(style=const.ACTIVE_VIEW_BUTTON)

    def disabled(self):
        if self.instate([const.NOTPRESSED]):
            return
        self.state([const.NOTPRESSED])
        self.config(style=const.VIEW_BUTTON)


class ViewNavigator(ttk.Frame):
    _buttons: list[ViewButton] = []

    def __init__(self, master):
        super().__init__(master, style=const.VIEW_NAVIGATOR)
        self.pack(side=tk.LEFT, anchor=tk.W, fill=tk.Y)
        self.bind('<<SwitchView>>', self.switch_view)

    def add_button(self, text: str = 'Placeholder'):
        btn = ViewButton(self, text, index=len(self._buttons))
        self._buttons.append(btn)
        return btn

    def switch_view(self, event: tk.Event):
        for btn in self._buttons:
            btn.active() if btn.index == event.state else btn.disabled()
