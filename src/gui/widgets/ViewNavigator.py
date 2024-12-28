from __future__ import annotations

from src.gui.views.View import View

import tkinter as tk
import tkinter.ttk as ttk

from abc import abstractmethod


class ViewButton(ttk.Button):
    buttons: list[ViewButton] = []
    active: int | None = None

    def __init__(
        self,
        master: ViewNavigator,
        view: View | None = None,
        text: str = '',
    ):
        super().__init__(master, text=text, command=self.click)
        self.pack(fill=tk.X, side=tk.TOP, ipady=4)
        self.index = len(self.buttons)
        self.buttons.append(self)
        self.view = view

    def click(self):
        for i, btn in enumerate(self.buttons):
            if i == self.index:
                self.active = i
                btn.disable()
                if btn.view is not None:
                    btn.view.pack()
            else:
                btn.enable()
                if btn.view is not None:
                    btn.view.hide()

    def enable(self):
        self.config(state=tk.NORMAL)

    def disable(self):
        self.config(state=tk.DISABLED)


class LazyButton(ViewButton):
    text: str = ''
    _view_widget: type[View]

    def __init__(self, master: ViewNavigator, top_level: tk.Tk | tk.Toplevel):
        super().__init__(master, view=None, text=self.text)
        self.top_level = top_level

    @abstractmethod
    def lazy_load_python_modules(self) -> None: ...

    def build_view_widget(self) -> View:
        return self._view_widget(self.top_level)

    def click(self):
        if self.view is None:
            self.lazy_load_python_modules()
            self.view = self.build_view_widget()
        super().click()


class ViewNavigator(ttk.Frame):
    def pack(self):
        super().pack(side=tk.LEFT, anchor=tk.W, fill=tk.Y)

    def add_button(self, text: str = '', widget: View | None = None) -> ViewButton:
        return ViewButton(self, widget, text)


class LazyViewNavigator(ViewNavigator):
    def __init__(self, master: tk.Tk | tk.Toplevel):
        super().__init__(master)
        self.parent_widget = master

    def add_button(
        self, button_class: type[LazyButton], *, invoke: bool = False
    ) -> LazyButton:
        btn = button_class(self, self.parent_widget)
        if invoke:
            btn.click()
        return btn
