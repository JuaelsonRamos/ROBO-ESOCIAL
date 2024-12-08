from __future__ import annotations

import src.gui.constants as const

from src.gui.views.View import View

import tkinter as tk
import tkinter.ttk as ttk

from typing import cast


class ViewButton(ttk.Button):
    def __init__(
        self,
        master: ViewNavigator,
        view: View | None = None,
        text: str = '',
        *,
        index: int,
    ):
        super().__init__(master, text=text, style=const.VIEW_BUTTON, command=self.click)
        self.pack(fill=tk.X, side=tk.TOP, ipady=4)
        self.index = index
        self.view = view
        self._pressed: bool = False
        if view is None:
            self.config(style=const.VIEW_BUTTON)

    def click(self):
        if self.view is None:
            return
        self.master.event_generate('<<SwitchView>>', state=self.index)

    def active(self):
        if self.view is None or self._pressed:
            return
        self._pressed = True
        self.config(style=const.ACTIVE_VIEW_BUTTON)

    def disabled(self):
        if self.view is None or not self._pressed:
            return
        self._pressed = False
        self.config(style=const.VIEW_BUTTON)


class ViewNavigator(ttk.Frame):
    _buttons: list[ViewButton] = []
    _active: int | None = None

    def __init__(self, master):
        super().__init__(master, style=const.VIEW_NAVIGATOR)
        self.pack(side=tk.LEFT, anchor=tk.W, fill=tk.Y)
        self.bind('<<SwitchView>>', self.switch_view)

    def add_button(self, text: str = '', widget: View | None = None) -> ViewButton:
        btn = ViewButton(self, widget, text, index=len(self._buttons))
        self._buttons.append(btn)
        return btn

    def switch_view(self, event: tk.Event) -> None:
        if self._active == event.state:
            return
        for btn in self._buttons:
            if btn.index == event.state:
                btn.active()
            else:
                btn.disabled()
        previous, current = self._active, cast(int, event.state)
        if previous is not None:
            btn = self._buttons[previous]
            cast(View, btn.view).hide()
        btn = self._buttons[current]
        cast(View, btn.view).pack()
        self._active = current
