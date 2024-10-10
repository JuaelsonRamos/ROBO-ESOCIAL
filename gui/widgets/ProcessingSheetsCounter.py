from __future__ import annotations

from gui.utils.units import padding

import tkinter as tk
import tkinter.ttk as ttk


class Counter:
    def set_counter(self, current: int):
        if current > self.total:
            raise ValueError(f'current value is greater than total ({self.total})')
        if current < 0:
            raise ValueError('current value is less than zero')
        self.current = current

    def set_total(self, total: int):
        if total < 0:
            raise ValueError('total is less than zero')
        self.total = total
        self.set_counter(self.current)  # force update

    def reset(self):
        self.current = self.total = 0


class LabelCounter(ttk.Label, Counter):
    def __init__(self, master):
        super().__init__(master, padding=padding(right=5))
        self.pack(side=tk.LEFT, anchor=tk.W)
        self.reset()

    def set_counter(self, current: int):
        super().set_counter(current)
        self.config(text=f'Processando ({self.current}/{self.total})')

    def reset(self):
        super().reset()
        self.config(text='Aguardando Processamento')


class Progress(ttk.Progressbar, Counter):
    def __init__(self, master):
        super().__init__(master, orient=tk.HORIZONTAL, phase=1, length=200)
        self.pack(side=tk.LEFT, anchor=tk.W)

    def set_counter(self, current: int):
        super().set_counter(current)
        self.config(value=self.current)

    def set_total(self, total: int):
        super().set_total(total)
        self.config(maximum=self.total)

    def reset(self):
        super().reset()
        self.config(maximum=0)


class ProcessingSheetsCounter(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(side=tk.LEFT, anchor=tk.W)
        self.conter = LabelCounter(self)
        self.progressbar = Progress(self)
