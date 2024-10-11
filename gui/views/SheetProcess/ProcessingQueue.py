from __future__ import annotations

import gui.state as state
import gui.views.SheetProcess.data as data

from gui.views.SheetProcess.InteractiveTreeList import InteractiveTreeList

import time
import tkinter as tk
import threading
import tkinter.filedialog as filedialog

from pathlib import Path


class ProcessingQueue(InteractiveTreeList):
    def __init__(self, master):
        super().__init__(
            master, 'Fila de Processamento', columns=data.input_queue.columns
        )

        self.create_add_button()
        self.add_button('Remover')
        self.add_button('Começar')
        self.add_button('Pausar')
        self.add_button('Parar')

    def create_add_button(self):
        self.files_event = threading.Event()
        self.files_lock = threading.Lock()
        self.files_add_event = threading.Event()
        self.files_stop_event = threading.Event()
        self.files_add_stop = threading.Event()

        add_btn = self.add_button('Adicionar')

        add_btn.config(command=self.files_event.set)
        self._files_thread = threading.Thread(
            name='files_choose', target=self.wait_files
        )
        self._files_add_thread = threading.Thread(
            name='files_add', target=self.add_files
        )

        state.thread.register(
            thread=self._files_thread, stop_event=self.files_stop_event
        )
        state.thread.register(
            thread=self._files_add_thread, stop_event=self.files_add_stop
        )
        self._files_thread.start()
        self._files_add_thread.start()

    def wait_files(self):
        while True:
            if self.files_stop_event.is_set():
                return
            if not self.files_event.is_set():
                time.sleep(0.5)
                continue
            with self.files_lock:
                self.files = filedialog.askopenfilenames()
                self.files_add_event.set()
                self.files_event.clear()

    def add_files(self):
        while True:
            if self.files_add_stop.is_set():
                return
            if not self.files_add_event.is_set():
                time.sleep(1)
                continue
            with self.files_lock:
                for filename in self.files:
                    data = self.make_row_data(filename)
                    self.tree.insert('', 'end', values=data)
            self.files_add_event.clear()

    def make_row_data(self, filename: str):
        path = Path(filename)
        data = []

        def add(key: str, value):
            data.insert(self.columns[key]['index'], value)

        add('list_order', 0)
        add('file_name', path.stem)
        add('file_type', path.suffix)
        add('storage_size', str(path.stat().st_size))
        add('date_added', str(time.time()))

        return data
