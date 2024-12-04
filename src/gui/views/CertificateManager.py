from __future__ import annotations

from src.certificate import copy_certificate, delete_certificate, get_certificates
from src.gui.lock import TkinterLock
from src.gui.utils.units import padding
from src.gui.views.View import View

import tkinter as tk
import functools
import tkinter.ttk as ttk

from pathlib import Path
from tkinter import filedialog
from typing import Sequence, cast


class Title(ttk.Label):
    def __init__(self, master: ttk.Widget):
        super().__init__(
            master, anchor=tk.CENTER, justify=tk.CENTER, text='Certificados'
        )
        self.pack(side=tk.TOP, fill=tk.X)


class ButtonFrame(ttk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master, height=10)

    def pack(self):
        super().pack(side=tk.TOP, fill=tk.X)

        p = padding(left=5, right=5)
        w = 15

        _add_item = functools.partial(self.tree.event_generate, '<<AddItem>>')
        self.add = ttk.Button(
            self,
            text='Adicionar',
            width=w,
            padding=p,
            command=_add_item,
        )

        _delete_item = functools.partial(self.tree.event_generate, '<<DeleteItem>>')
        self.delete = ttk.Button(
            self,
            text='Deletar',
            width=w,
            padding=p,
            command=_delete_item,
        )

        _reload_tree = functools.partial(self.tree.event_generate, '<<ReloadTree>>')
        self.reload = ttk.Button(
            self,
            text='Atualizar',
            width=w,
            padding=p,
            command=_reload_tree,
        )

        self.delete.pack(side=tk.LEFT)
        self.add.pack(side=tk.LEFT, before=self.delete)
        self.reload.pack(side=tk.LEFT, after=self.delete)

    @property
    def tree(self) -> CertificateList:
        return self.master.tree  # type: ignore


class CertificateList(ttk.Treeview):
    def __init__(self, master: ttk.Widget):
        super().__init__(
            master,
            show='headings',
            columns=('index', 'name', 'type'),
            selectmode='browse',
        )

    def pack(self):
        super().pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        self.heading('index', text='#', anchor=tk.CENTER)
        self.column('index', anchor=tk.CENTER, minwidth=50)

        self.heading('name', text='Nome', anchor=tk.W)
        self.column('name', anchor=tk.W, minwidth=200)

        self.heading('type', text='Tipo', anchor=tk.CENTER)
        self.column('type', anchor=tk.CENTER, minwidth=80)

        self.bind('<<TreeviewSelect>>', self._update_select)
        self.bind('<<ReloadTree>>', self.reload)
        self.bind('<<DeleteItem>>', self.delete_focused)
        self.bind('<<AddItem>>', self.add_item)

    @property
    def button(self) -> ButtonFrame:
        return self.master.button  # type: ignore

    def get_certs(self) -> Sequence[Path]:
        certs = get_certificates()
        by_creation_time = sorted(certs, key=lambda path: path.stat().st_ctime)
        return by_creation_time

    def reload(self, event: tk.Event):
        for i, cert in enumerate(self.get_certs()):
            sha = cert.stem.lower()
            if self.exists(sha):
                continue
            cert_type = cert.suffix.removeprefix('.').upper()
            self.insert('', i, sha, values=(i, sha, cert_type))

    def delete_focused(self, event: tk.Event):
        iid = self.focus()
        if iid == '':
            return
        certs = self.get_certs()
        p = certs[self.index(iid)]
        delete_certificate(p)
        self.delete(iid)

    def _open_files(self) -> tuple[str, ...]:
        files = filedialog.askopenfilenames(
            defaultextension='*.pem',
            filetypes=(('Certificado digital', ('*.crt', '*.pem')),),
            parent=self,
            title='Selecione um certificado digital',
        )
        return tuple() if files == '' else files

    def _insert_files(self, value: tuple[str, ...] | Exception, raised: bool) -> None:
        if raised:
            raise cast(Exception, value)
        value = cast(tuple[str, ...], value)
        for v in value:
            copy_certificate(v)

    def add_item(self, event: tk.Event):
        lock = TkinterLock()
        lock.schedule(self, self._open_files, self._insert_files)

    def _update_select(self, event: tk.Event):
        if self.focus() == '':
            self.button.delete.state([tk.DISABLED])
            return
        self.button.delete.state([tk.ACTIVE])


class CertificateManager(View):
    def __init__(self, master):
        super().__init__(master)
        self.tree = CertificateList(self)
        self.tree.pack()
        self.button = ButtonFrame(self)
        self.button.pack()
        self.button.pack_configure(before=self.tree)
