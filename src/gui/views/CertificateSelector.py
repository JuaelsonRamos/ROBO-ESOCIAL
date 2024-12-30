from __future__ import annotations

from src.certificate import CertificateHelper
from src.gui.utils.units import padding

import tkinter as tk

from dataclasses import dataclass
from tkinter import ttk
from typing import Any, Callable


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
        self.columns = ('issued_by', 'issued_to', 'is_expired')
        super().__init__(master, columns=self.columns, show='headings', height=10)
        self._selected: int | None = None
        self.bind('<Visibility>', self.fill_tree)
        self.bind('<Motion>', self._prevent_resizing)
        self.bind('<Button-1>', self._prevent_resizing)
        self.bind('<ButtonRelease-1>', self._prevent_resizing)
        self.heading('issued_by', text='Emitido Por', anchor=tk.W)
        self.column('issued_by', anchor=tk.W, minwidth=150, width=150)
        self.heading('issued_to', text='Emitido Para', anchor=tk.W)
        self.column('issued_to', anchor=tk.W, minwidth=150, width=150)
        self.heading('is_expired', text='Já expirou?', anchor=tk.CENTER)
        self.column('is_expired', anchor=tk.CENTER, minwidth=80, width=80)

    def _prevent_resizing(self, event: tk.Event):
        if self.identify_region(event.x, event.y) == 'separator':
            return 'break'

    def fill_tree(self, event: tk.Event | None = None):
        cert_helper = CertificateHelper()
        br_certs = cert_helper.get_br_ca_cert_dicts()
        sorted = cert_helper.sort_ca_cert_dict_sequence(br_certs)
        md5_cert = cert_helper.get_md5_of_many_ca_cert_dicts(sorted)
        for i, pair in enumerate(md5_cert):
            md5, cert = pair
            info = CertificateHelper.parse_ca_issuer_subject_info(cert)
            values = (
                info['issuer']['organizationName'],
                info['subject']['organizationName'],
                'Sim' if cert_helper.is_expired(cert) else 'Não',
            )
            if self.exists(md5):
                self.item(md5, values=values)
                continue
            self.insert('', i, md5, values=values)
        md5_set = set(pair[0] for pair in md5_cert)
        excess = md5_set.difference(self.get_children())
        if len(excess) == 0:
            return
        self.delete(*excess)


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


class CertificateSelector(ttk.Frame):
    def __init__(
        self, master: CertificateSelectorWindow, callback: Callable[[str], Any]
    ):
        super().__init__(master)
        self.toplevel = master
        self.submit_callback = callback
        # main content of container
        self.tree = CertificateList(self)
        self.tree.bind('<<TreeviewSelect>>', self._enable_buttons)
        self.tree.bind('<Visibility>', self._enable_buttons, '+')
        self.scroll = ttk.Scrollbar(self)
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        self.scroll.pack(side=tk.LEFT, fill=tk.Y)
        # inside button frame
        self.cancel_btn = ttk.Button(
            self.button_frame, command=self.toplevel.close_window, text='Cancelar'
        )
        self.submit_btn = ttk.Button(
            self.button_frame, command=self._call_submit, text='Selecionar'
        )
        self.update_btn = ttk.Button(
            self.button_frame, command=self.tree.fill_tree, text='Atualizar'
        )

        self.submit_btn.pack(side=tk.LEFT, ipady=2, ipadx=5)
        self.update_btn.pack(side=tk.LEFT, ipady=2, ipadx=5)
        self.cancel_btn.pack(
            side=tk.LEFT, ipady=2, ipadx=5, anchor=tk.E, expand=tk.TRUE
        )
        # relate tree to scrollbar
        self.scroll.config(command=self.tree.yview)
        self.tree.config(xscrollcommand=self.scroll.set)

    def _enable_buttons(self, event: tk.Event):
        if self.tree.focus() == '':
            self.submit_btn.config(state=tk.DISABLED)
            return
        self.submit_btn.config(state=tk.ACTIVE)

    def _call_submit(self):
        md5 = self.tree.focus()
        if md5 == '':
            return
        self.submit_callback(md5)


class CertificateSelectorWindow(tk.Toplevel):
    def __init__(
        self,
        master: ttk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        submit_callback: Callable[[str], Any],
    ):
        super().__init__(master)
        self.parent_window = parent_window
        self.submit_callback = submit_callback
        self.frame = CertificateSelector(self, self.submit_callback)
        self.frame.pack(side=tk.LEFT, expand=tk.TRUE, fill=tk.BOTH)
        self.config_window()

    def close_window(self):
        self.update()
        self.grab_release()
        self.destroy()
        self.update()

    def config_window(self):
        global _widgets
        self.protocol('WM_DELETE_WINDOW', self.close_window)
        self.title('Certificado que será usado')
        self.state(tk.NORMAL)
        self.config(takefocus=tk.TRUE)
        self.resizable(width=True, height=True)
        self.minsize(400, 450)
        self.maxsize(500, 450)
        self.transient(self.parent_window)
        self.grab_set()
