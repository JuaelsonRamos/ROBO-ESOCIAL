from __future__ import annotations

from src.certificate import copy_certificate, delete_certificate, get_certificates
from src.gui.lock import TkinterLock
from src.gui.utils.units import padding
from src.gui.views.View import View
from src.windows import open_file_dialog

import tkinter as tk
import functools
import tkinter.ttk as ttk

from pathlib import Path
from typing import Final, Sequence, cast


_common_padding: Final[int] = 5


class CommonBase(ttk.Widget):
    @property
    def tree(self) -> CertificateList:
        return self.master.tree  # type: ignore

    @property
    def buttons(self) -> ButtonFrame:
        return self.master.buttons  # type: ignore

    @property
    def title(self) -> Title:
        return self.master.title  # type: ignore


class Title(CommonBase, ttk.Label):
    def __init__(self, master: ttk.Widget):
        super().__init__(
            master, anchor=tk.CENTER, justify=tk.CENTER, text='Certificados'
        )

    def pack(self):
        super().pack(
            side=tk.TOP, fill=tk.X, ipady=_common_padding * 2, anchor=tk.CENTER
        )


class ButtonFrame(CommonBase, ttk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)

    def pack(self):
        super().pack(
            side=tk.TOP,
            anchor=tk.CENTER,
            before=self.tree,
            padx=_common_padding,
            pady=_common_padding,
        )

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


class CertificateList(CommonBase, ttk.Treeview):
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

    def get_certs(self) -> Sequence[Path]:
        certs = get_certificates()
        by_creation_time = sorted(certs, key=lambda path: path.stat().st_ctime)
        return by_creation_time

    def reload(self, event: tk.Event):
        for i, cert in enumerate(self.get_certs()):
            sha = cert.stem.lower()  # regular file name if __debug__, else SHA hash
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

    def _insert_files(self, value: tuple[str, ...] | Exception, raised: bool) -> None:
        if raised:
            raise cast(Exception, value)
        value = cast(tuple[str, ...], value)
        for v in value:
            copy_certificate(v)
        self.event_generate('<<ReloadTree>>')

    def add_item(self, event: tk.Event):
        lock = TkinterLock()
        func = functools.partial(
            open_file_dialog,
            hwnd=self.winfo_id(),
            title='Selecione um certificado digital',
            extensions=[
                ('Certificado digital', ('*.crt', '*.pem', '*.pfx')),
            ],
            multi_select=True,
        )
        lock.schedule(self, func, self._insert_files, block=False)

    def _update_select(self, event: tk.Event):
        if self.focus() == '':
            self.buttons.delete.state([tk.DISABLED])
            return
        self.buttons.delete.state([tk.ACTIVE])


class CertificateManager(View):
    def __init__(self, master):
        super().__init__(master)
        self.title = Title(self)
        self.tree = CertificateList(self)
        self.button = ButtonFrame(self)
        self.pack_in_order()

    def pack_in_order(self):
        """Packs widgets in the strict order in which they need to."""
        self.title.pack()
        self.tree.pack()
        self.button.pack()
