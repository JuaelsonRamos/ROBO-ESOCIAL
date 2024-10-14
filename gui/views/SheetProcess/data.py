from __future__ import annotations

import tkinter as tk

from typing import TypedDict


class Heading(TypedDict):
    text: str
    index: int
    anchor: str
    width: int
    minwidth: int


class input_queue:
    columns: dict[str, Heading] = {
        'list_order': {
            'text': '#',
            'index': 0,
            'anchor': tk.CENTER,
            'minwidth': 28,
            'width': 28,
        },
        'file_name': {
            'text': 'Nome',
            'index': 1,
            'anchor': tk.W,
            'minwidth': 250,
            'width': 350,
        },
        'file_type': {
            'text': 'Tipo',
            'index': 2,
            'anchor': tk.CENTER,
            'minwidth': 80,
            'width': None,
        },
        'storage_size': {
            'text': 'Tamanho',
            'index': 2,
            'anchor': tk.CENTER,
            'minwidth': 80,
            'width': None,
        },
        'date_added': {
            'text': 'Adicionado',
            'index': 4,
            'anchor': tk.CENTER,
            'minwidth': 150,
            'width': 180,
        },
    }

    @classmethod
    @property
    def column_list(self) -> list[Heading]:
        return list(self.columns.values())


class history:
    columns: tuple[Heading, ...] = {
        'list_order': {
            'text': 'Ordem',
            'index': 0,
            'anchor': tk.E,
            'minwidth': 50,
            'width': 80,
        },
        'file_name': {
            'text': 'Nome',
            'index': 1,
            'anchor': tk.W,
            'minwidth': 250,
            'width': 350,
        },
        'file_type': {
            'text': 'Tipo',
            'index': 2,
            'anchor': tk.CENTER,
            'minwidth': 80,
            'width': None,
        },
        'storage_size': {
            'text': 'Tamanho',
            'index': 2,
            'anchor': tk.CENTER,
            'minwidth': 80,
            'width': None,
        },
        'date_started': {
            'text': 'Iniciado',
            'index': 4,
            'anchor': tk.CENTER,
            'minwidth': 150,
            'width': 180,
        },
        'date_finished': {
            'text': 'Finalizado',
            'index': 5,
            'anchor': tk.CENTER,
            'minwidth': 150,
            'width': 180,
        },
    }

    @classmethod
    @property
    def column_list(self) -> list[Heading]:
        return list(self.columns.values())
