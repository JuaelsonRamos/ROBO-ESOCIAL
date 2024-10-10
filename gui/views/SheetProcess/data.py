from __future__ import annotations

import tkinter as tk

from dataclasses import dataclass
from typing import TypedDict


class Heading(TypedDict):
    text: str
    index: int
    anchor: str
    width: int
    minwidth: int


@dataclass(frozen=True, init=False)
class input_queue:
    columns: tuple[Heading, ...] = (
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
    )
