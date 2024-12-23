from __future__ import annotations

from src.db import ClientCertificate
from src.gui.utils.units import padding

import tkinter as tk

from dataclasses import dataclass
from itertools import zip_longest
from tkinter import ttk
from typing import Callable, cast


@dataclass(frozen=False, slots=True)
class WidgetNamespace:
    tree: CertificateList
    scroll: ttk.Scrollbar
    submit: SubmitButton
    cancel: CancelButton
    frame: CertificateSelector


# should be assigned upon main widget initialization
_widgets: WidgetNamespace = None  # type: ignore


class CertificateList(ttk.Treeview):
    def __init__(self, master: CertificateSelector):
        self.columns = ('index', 'description', 'type')
        super().__init__(master, columns=self.columns, show='tree', height=10)
        self._selected: int | None = None
        self.bind('<Motion>', 'break')
        self.bind('<Visibility>', self.fill_tree)
        self.bind('<<TreeviewSelect>>', self._notify_selection)
        self.bind('<<ClearSelection>>', self._clear_selection)
        self.heading('index', text='#', anchor=tk.CENTER)
        self.column('index', anchor=tk.CENTER, minwidth=32, width=32)
        self.heading('description', text='Descrição', anchor=tk.W)
        self.column('description', anchor=tk.W, minwidth=150, width=150)
        self.heading('type', text='Tipo', anchor=tk.CENTER)
        self.column('type', anchor=tk.CENTER, minwidth=50, width=50)

    def fill_tree(self, event: tk.Event):
        if ClientCertificate.sync_count() == 0:
            return
        rows = ClientCertificate.sync_select_all_columns(
            '_id', 'description', 'using_type'
        )
        rows = sorted(rows, key=lambda r: r[0])  # sort by _id
        iids = sorted(int(iid) for iid in self.get_children())
        for row, iid in zip_longest(rows, iids, fillvalue=None):
            if row is None:
                # too many iids for not as much rows, delete items
                iid = cast(int, iid)  # if row is None, then iid isn't
                self.delete(iid)
                continue
            values = (str(row._id), row.description, row.using_type)
            if iid is None:
                # not enough items for too many db rows
                self.insert('', 'end', row._id, values=values)
                continue
            # item with iid=_id already exist, so modify it
            self.item(row._id, values=values)

    def _notify_selection(self, event: tk.Event):
        global _widgets
        _widgets.submit.event_generate('<<SetSelection>>', state=self.focus())

    def _clear_selection(self, event: tk.Event):
        selection = self.selection()
        if len(selection) == 0:
            return
        self.focus('')
        self.selection_remove(selection)


class ActionButton(ttk.Button):
    def __init__(self, master: ttk.Frame):
        super().__init__(master, width=15, padding=padding(horizontal=5))


class SubmitButton(ActionButton):
    def __init__(self, master: ttk.Frame):
        super().__init__(master)
        self.config(text='Selecionar')
        self.selected: int | None = None
        self.bind('<<SetSelection>>', self._set_selected)

    def _set_selected(self, event: tk.Event):
        if event.state == '':
            self.selected = None
            self.config(state=tk.DISABLED)
            return
        try:
            self.selected = int(event.state)
            self.config(state=tk.NORMAL)
        except Exception as err:
            self.selected = None
            self.config(state=tk.DISABLED)
            raise err


class CancelButton(ActionButton):
    def __init__(self, master: ttk.Frame):
        super().__init__(master)
        self.config(text='Cancelar')
        self.bind('<<CancelSelection>>', self._unset_selection)

    def _unset_selection(self, event: tk.Event):
        global _widgets
        _widgets.tree.event_generate('<<ClearSelection>>', state='')


class GoToButton(ActionButton):
    # TODO
    pass


class SearchBar(ttk.Entry):
    # TODO
    pass


class CertificateSelector(ttk.Frame):
    def __init__(self, master: tk.Toplevel):
        super().__init__(master)
        # main content of container
        self.tree = CertificateList(self)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        self.scroll = ttk.Scrollbar(self)
        self.scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        # inside button frame
        self.cancel = CancelButton(self.button_frame)
        self.cancel.pack(side=tk.RIGHT)
        self.submit = SubmitButton(self.button_frame)
        self.submit.pack(side=tk.RIGHT, before=self.cancel)
        # relate tree to scrollbar
        self.scroll.config(command=self.tree.xview)
        self.tree.config(xscrollcommand=self.scroll.set)


class CertificateSelectorWindow(tk.Toplevel):
    def __init__(
        self,
        master: ttk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        run_on_submit: Callable[[int], None],
    ):
        super().__init__(master)
        self.run_on_submit = run_on_submit
        self.parent_window = parent_window
        self.create_widgets()
        self.config_window()

    def create_widgets(self):
        global _widgets

        # main container of window
        self.frame = CertificateSelector(self)
        self.frame.pack(side=tk.LEFT, expand=tk.TRUE, fill=tk.BOTH)

        # assign actions
        self.frame.cancel.config(command=self.close)
        self.frame.submit.config(command=self.submit)

        # init widget references
        _widgets = WidgetNamespace(
            self.frame.tree,
            self.frame.scroll,
            self.frame.submit,
            self.frame.cancel,
            self.frame,
        )

    def config_window(self):
        global _widgets
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.title('Certificado que será usado')
        self.state(tk.NORMAL)
        self.config(takefocus=tk.TRUE)
        self.resizable(width=True, height=True)
        self.minsize(300, 400)
        self.maxsize(450, 600)
        self.transient(self.parent_window)

    def close(self):
        self.frame.tree.event_generate('<<ClearSelection>>')
        self.update()
        self.destroy()
        self.update()

    def submit(self):
        iid = self.frame.submit.selected
        if iid is None:
            return
        self.run_on_submit(iid)
        self.close()
