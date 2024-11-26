from __future__ import annotations

import src.gui.views.SheetProcess.data as data

from src.gui.asyncio import Thread
from src.gui.views.SheetProcess.InteractiveTreeList import InteractiveTreeList

import time
import tkinter as tk
import threading
import tkinter.filedialog as filedialog

from pathlib import Path


class ProcessingQueue(InteractiveTreeList):
    def __init__(self, master):
        super().__init__(master, 'Fila de Processamento', columns=data.INPUT_QUEUE)

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

    def make_row_data(self, filename: str):
        # TODO generic, inherited way of making row data
        path = Path(filename)
        data = []
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
