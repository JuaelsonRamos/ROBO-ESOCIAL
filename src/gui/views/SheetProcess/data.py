from __future__ import annotations

import tkinter as tk

from typing import TypedDict


class Heading(TypedDict):
    text: str
    iid: str
    anchor: str
    width: int | None
    minwidth: int | None


HeadingSequence = tuple[Heading, ...]


INPUT_QUEUE: HeadingSequence = (
    {
        'text': '#',
        'iid': 'list_order',
        'anchor': tk.CENTER,
        'minwidth': 28,
        'width': 28,
    },
    {
        'text': 'Nome',
        'iid': 'file_name',
        'anchor': tk.W,
        'minwidth': 250,
        'width': 350,
    },
    {
        'text': 'Tipo',
        'iid': 'file_type',
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Tamanho',
        'iid': 'storage_size',
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Adicionado',
        'iid': 'date_added',
        'anchor': tk.CENTER,
        'minwidth': 150,
        'width': 180,
    },
)


HISTORY: HeadingSequence = (
    {
        'text': 'Ordem',
        'iid': 'list_order',
        'anchor': tk.E,
        'minwidth': 50,
        'width': 80,
    },
    {
        'text': 'Nome',
        'iid': 'file_name',
        'anchor': tk.W,
        'minwidth': 250,
        'width': 350,
    },
    {
        'text': 'Tipo',
        'iid': 'file_type',
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Tamanho',
        'iid': 'storage_size',
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Iniciado',
        'iid': 'date_started',
        'anchor': tk.CENTER,
        'minwidth': 150,
        'width': 180,
    },
    {
        'text': 'Finalizado',
        'iid': 'date_finished',
        'anchor': tk.CENTER,
        'minwidth': 150,
        'width': 180,
    },
)
