from __future__ import annotations

import src.gui.constants as const

from src.gui.asyncio import Thread
from src.gui.utils.units import padding
from src.gui.views.View import View
from src.utils import extract_from

import time
import tkinter as tk
import threading
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog

from pathlib import Path
from typing import Any, TypedDict


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


class QueueButton(ttk.Button):
    def __init__(self, master: ttk.Widget, text: str):
        super().__init__(master, text=text)
        # NOTE side=RIGHT orders things in reverse, instead of just justifying position
        self.pack(side=tk.RIGHT)

    def before(self, button: ttk.Widget) -> None:
        self.pack_configure(before=button)


class QueueButtonRow(ttk.Frame):
    def __init__(self, master: ttk.Widget, text: str):
        super().__init__(master)
        self._buttons: list[ttk.Button] = []
        self.text = text
        self.pack(anchor=tk.NE, side=tk.TOP, fill=tk.X)
        self.create_widgets()

    def add_button(self, text: str = 'Placeholder') -> ttk.Button:
        btn = QueueButton(self, text)
        if len(self._buttons) > 0:
            btn.before(self._buttons[-1])
        self._buttons.append(btn)
        return btn

    def create_widgets(self):
        label = ttk.Label(self, text=self.text.upper(), padding=padding(left=5))
        label.pack(side=tk.LEFT, anchor=tk.W, fill=tk.Y)


class InteractiveTreeList(ttk.Frame):
    def __init__(self, master: ttk.Widget, title: str, *, columns: HeadingSequence):
        super().__init__(master)
        self.columns = columns
        self.title = title
        self.pack(fill=tk.BOTH, expand=tk.TRUE, side=tk.TOP, anchor=tk.NW)
        self.button_row = QueueButtonRow(self, self.title)
        self.tree = ShortTree(self, columns=columns)

    def add_button(self, text: str) -> ttk.Button:
        return self.button_row.add_button(text)


class ProcessingQueue(InteractiveTreeList):
    def __init__(self, master):
        super().__init__(master, 'Fila de Processamento', columns=INPUT_QUEUE)

        self._index = self._gen_next_index()

        self.create_add_button()
        self.create_delete_button()
        self.add_button('Começar')
        self.add_button('Pausar')
        self.add_button('Parar')

    def create_add_button(self):
        self.files_lock = threading.Lock()

        add_btn = self.add_button('Adicionar')

        self._files_thread = Thread(
            name='files_choose', target=self.wait_files, attempt_delay=1.0
        )
        self._files_add_thread = Thread(
            name='files_add', target=self.add_files, attempt_delay=0.5
        )

        add_btn.config(command=self._files_thread.events.start.set)

        self._files_thread.start()
        self._files_add_thread.start()

    def create_delete_button(self):
        btn = self.add_button('Remover')

        def delete_focused():
            cell = self.tree.focus()
            if not cell or not self.tree.exists(cell):
                return
            self.tree.delete(cell)

        btn.config(command=delete_focused)

    def wait_files(self):
        with self.files_lock:
            self.files = filedialog.askopenfilenames(
                parent=self,
                title='Selecione um arquivo de planilha de dados',
                defaultextension='.xlsx',
                filetypes=[('Todos os arquivos', '*'), ('Arquivo Excel', '.xlsx .xls')],
            )
            self._files_add_thread.events.start.set()

    def add_files(self):
        with self.files_lock:
            for filename in self.files:
                data = self.make_row_data(filename)
                self.tree.insert('', 'end', values=data)

    def _gen_next_index(self):
        i = 1
        while True:
            yield i
            i += 1

    def make_row_data(self, filename: str) -> list[Any]:
        # TODO generic, inherited way of making row data
        path = Path(filename)
        data: list[Any] = []
        add = data.append
        for col in self.columns:
            match col['iid']:
                case 'list_order':
                    add(next(self._index))
                case 'file_name':
                    add(path.stem)
                case 'file_type':
                    add(path.suffix)
                case 'storage_size':
                    add(str(path.stat().st_size))
                case 'date_added':
                    add(str(time.time()))
        return data


class HistoryList(InteractiveTreeList):
    def __init__(self, master):
        super().__init__(master, 'Histórico', columns=HISTORY)
        self.add_button('Exportar Planilha')
        self.add_button('Exportar Histórico')


class ShortTree(ttk.Treeview):
    min_height = 10
    """Altura mínima em células."""

    def __init__(self, master: ttk.Widget, *, columns: HeadingSequence):
        self.columns = columns
        self._columns_order = tuple(col['iid'] for col in columns)

        super().__init__(
            master,
            style=const.SHORT_TREE,
            height=self.min_height,
            selectmode=tk.EXTENDED,
            takefocus=tk.TRUE,
            columns=self._columns_order,
            show='headings',
        )
        self.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)

        for col in columns:
            self.heading(col['iid'], **extract_from(col, 'text', 'anchor'))
            self.column(
                col['iid'],
                stretch=tk.FALSE,
                **extract_from(col, 'width', 'minwidth'),
            )

        # empty = ['' for _ in range(self.min_height)]
        # for i in range(self.min_height):
        #     self.insert('', i, values=empty.copy())


class SheetProcess(View):
    def __init__(self, master):
        super().__init__(master, style=const.VIEW)
        self.create_widgets()

    def create_widgets(self):
        ProcessingQueue(self)
        HistoryList(self)
