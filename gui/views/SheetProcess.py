from __future__ import annotations

import gui.constants as const

import tkinter as tk
import tkinter.ttk as ttk

from typing import TypedDict


class Heading(TypedDict):
    text: str
    index: int
    anchor: str
    width: int
    minwidth: int


columns: list[Heading] = [
    {
        'text': 'Ordem',
        'index': 0,
        'anchor': tk.E,
        'minwidth': 50,
        'width': 80,
    },
    {
        'text': 'Nome',
        'index': 1,
        'anchor': tk.W,
        'minwidth': 250,
        'width': 350,
    },
    {
        'text': 'Tipo',
        'index': 2,
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Tamanho',
        'index': 2,
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Adicionado',
        'index': 4,
        'anchor': tk.CENTER,
        'minwidth': 150,
        'width': 180,
    },
]


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


class ShortTree(ttk.Treeview):
    min_height = 10
    """Altura mínima em células."""

    def __init__(self, master, *, columns: list[Heading]):
        self._columns_order = []
        for col in columns:
            self._columns_order.insert(col['index'], col['text'])

        super().__init__(
            master,
            style=const.SHORT_TREE,
            height=self.min_height,
            selectmode=tk.EXTENDED,
            takefocus=tk.TRUE,
            columns=self._columns_order,
            padding=2,
            show='headings',
        )
        self.pack(side=tk.TOP, fill=tk.X)

        for col in columns:
            self.heading(col['text'], text=col['text'], anchor=col['anchor'])
            self.column(
                col['text'],
                stretch=tk.FALSE,
                minwidth=col['minwidth'],
                width=col['minwidth'],
            )

        empty = ['' for _ in range(self.min_height)]
        for i in range(self.min_height):
            self.insert('', i, values=empty.copy())


class ProcessingQueue(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.X, side=tk.TOP, anchor=tk.NW)
        self.create_widgets()

    def create_widgets(self):
        button_row = QueueButtonRow(self)
        button_row.add_button('Adicionar')
        button_row.add_button('Remover')
        button_row.add_button('Começar')
        button_row.add_button('Pausar')
        button_row.add_button('Parar')

        ShortTree(self, columns=columns)


class SheetProcess(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style=const.VIEW)
        self.pack(fill=tk.BOTH, expand=tk.TRUE)
        self.create_widgets()

    def create_widgets(self):
        ProcessingQueue(self)
