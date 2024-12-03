from __future__ import annotations

import tkinter as tk

from tkinter import ttk


class View(ttk.Frame):
    def pack(self) -> None:
        super().pack(fill=tk.BOTH, expand=tk.TRUE, side=tk.RIGHT)

    def hide(self) -> None:
        self.pack_forget()
