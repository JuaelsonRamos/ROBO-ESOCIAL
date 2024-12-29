from __future__ import annotations

from src.gui.utils.units import padding

import tkinter as tk

from tkinter import ttk


class View(ttk.Frame):
    def __init__(self, master: tk.Tk | tk.Toplevel, title: str):
        super().__init__(master)
        self.title_frame = ttk.Frame(self, padding=padding(left=15))
        self.title = ttk.Label(
            self.title_frame, anchor=tk.W, justify=tk.LEFT, text=title
        )
        self.content_frame = ttk.Frame(self)

    def pack(self) -> None:
        super().pack(fill=tk.BOTH, expand=tk.TRUE, side=tk.RIGHT)
        self.title_frame.pack(side=tk.TOP, fill=tk.X, ipady=5)
        self.title.pack(side=tk.LEFT, fill=tk.X)
        self.content_frame.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE, padx=5, pady=5
        )

    def hide(self) -> None:
        self.pack_forget()
