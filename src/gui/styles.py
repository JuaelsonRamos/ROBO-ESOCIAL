from __future__ import annotations

import gui.constants as const

from utils.decorators import block

import tkinter as tk
import tkinter.ttk as ttk


style = ttk.Style()


def default():
    style.theme_use('default')


@block
def default_theme():
    style.theme_use('default')
    style.configure(const.VIEW_BUTTON, anchor=tk.W, width=15, relief=tk.RAISED)
    style.configure(const.ACTIVE_VIEW_BUTTON, anchor=tk.W, width=15, relief=tk.SUNKEN)
    style.configure(const.VIEW_NAVIGATOR)
    style.configure(const.SHORT_TREE_HEADING, padding=[5, 2])
    style.configure(const.SHORT_TREE_CELL, padding=[5, 2])
    style.configure(const.VIEW, background='black')
