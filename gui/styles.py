from __future__ import annotations

from utils.decorators import block

import tkinter as tk
import tkinter.ttk as ttk


style = ttk.Style()


def default():
    style.theme_use('default')


@block
def default_theme():
    style.theme_use('default')
    style.configure('ViewButton.TButton', anchor=tk.W, width=15)
    style.configure('ViewNavigator.TFrame')
