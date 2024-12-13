from __future__ import annotations

from src.certificate import copy_certificate, delete_certificate, get_certificates
from src.db import ClientCertificate
from src.gui.global_runtime_constants import GlobalRuntimeConstants
from src.gui.lock import TkinterLock
from src.gui.utils.units import padding
from src.gui.views.View import View
from src.windows import open_file_dialog

import math
import tkinter as tk
import functools
import itertools
import tkinter.ttk as ttk

from pathlib import Path
from typing import Final, Sequence, cast

from sqlalchemy import func


_common_padding: Final[int] = 5


class DatabaseHelper:
    def __init__(self):
        super().__init__()
        self.metadata = ClientCertificate.metadata
        self.table = self.metadata.tables['clientcertificate']

    @property
    def engine(self):
        if not GlobalRuntimeConstants.is_initialized():
            return
        return GlobalRuntimeConstants().sqlite  # type:ignore

    def count_certificates(self) -> int:
        with self.engine.begin() as conn:
            query = func.count().select().select_from(ClientCertificate._id)
            quantity = conn.scalar(query)
            return quantity or 0

    def get_all_certificates(self) -> Sequence[ClientCertificate]:
        with self.engine.begin() as conn:
            query = self.table.select()
            certs = conn.scalars(query).all()
            return certs

    def get_certificates(self, ids: Sequence[int]) -> Sequence[ClientCertificate]:
        with self.engine.begin() as conn:
            query = self.table.select().where(ClientCertificate._id.in_(ids))
            certs = conn.scalars(query).all()
            return certs


db_helpers = DatabaseHelper()


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
            after=self.title,
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
        self.columns = (
            'index',
            'created',
            'last_modified',
            'origin',
            'type',
            'has_public_key',
            'has_passphrase',
        )
        super().__init__(
            master,
            show='headings',
            columns=self.columns,
            selectmode='browse',
        )
        # prevents column resizing
        # SEE https://stackoverflow.com/a/71710427/15493645
        self.bind('<Motion>', 'break')
        self._define_headings()
        self.bind('<<TreeviewSelect>>', self._update_select)
        self.bind('<<ReloadTree>>', self.reload)
        self.bind('<<DeleteItem>>', self.delete_focused)
        self.bind('<<AddItem>>', self.add_item)

    def pack(self):
        super().pack(fill=tk.Y, side=tk.LEFT)

    def _define_headings(self):
        self.heading('index', text='#', anchor=tk.CENTER)
        self.column('index', anchor=tk.CENTER, width=32)

        self.heading('created', text='Data de Criação', anchor=tk.CENTER)
        self.column('created', anchor=tk.CENTER, width=150)

        self.heading('last_modified', text='Data Ultima Modificação', anchor=tk.CENTER)
        self.column('last_modified', anchor=tk.CENTER, width=150)

        self.heading('origin', text='URL', anchor=tk.W)
        self.column('origin', anchor=tk.CENTER, minwidth=200, width=300)

        self.heading('type', text='Tipo', anchor=tk.CENTER)
        self.column('type', anchor=tk.CENTER, width=50)

        self.heading(
            'has_public_key', text='Chave Pública Registrada', anchor=tk.CENTER
        )
        self.column('has_public_key', anchor=tk.CENTER, minwidth=200, width=200)

        self.heading('has_passphrase', text='Senha Registrada', anchor=tk.CENTER)
        self.column('has_passphrase', anchor=tk.CENTER, minwidth=200, width=200)

    def get_certs(self) -> Sequence[Path]:
        certs = get_certificates()
        by_creation_time = sorted(certs, key=lambda path: path.stat().st_ctime)
        return by_creation_time

    def _make_item_tree_data(self, cert: ClientCertificate) -> tuple[str, ...]:
        datetime_format = '%d/%m/%Y %H:%M'
        _id = str(cert._id)
        if cert.pfx is not None:
            _type = 'PFX'
        else:
            _type = Path(cert.cert_path).suffix.strip('.').upper()
        has_public_key = 'Sim' if cert.key is not None else 'Não'
        has_passphrase = 'Sim' if cert.passphrase is not None else 'Não'

        return (
            _id,
            cert.created.strftime(datetime_format),
            cert.last_modified.strftime(datetime_format),
            cert.origin,
            _type,
            has_public_key,
            has_passphrase,
        )

    def reload(self, event: tk.Event):
        count = db_helpers.count_certificates()
        if count == 0:
            return
        certs = db_helpers.get_all_certificates()
        for cert in certs:
            iid = str(cert._id)
            if self.exists(iid):
                self.item(iid, values=self._make_item_tree_data(cert))
                continue
            i = cert._id
            self.insert('', i, iid, values=self._make_item_tree_data(cert))

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


class TreeFrame(tk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.tree = CertificateList(self)  # type: ignore
        self.bind('<Visibility>', self.resize)

    def resize(self, event: tk.Event | None = None):
        window_size = self.master.winfo_width()
        self.max_width = math.ceil(window_size * 0.5)
        self.config(width=self.max_width)

    def pack(self):
        super().pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        self.pack_propagate(tk.FALSE)
        self.tree.pack()


class FormEntry:
    _get_class_instance_number = itertools.count(0).__next__
    entries: list[FormEntry] = []
    label_width: int = 25
    entry_width: int = 35

    def __init__(
        self,
        master: CertificateForm,
        label_text: str | None = None,
    ):
        self.index = self._get_class_instance_number()
        self.entries.append(self)

        self.master = master

        self._var_label = tk.StringVar(value=label_text or 'Static Data Field:')
        self.label = ttk.Label(
            master,
            anchor=tk.E,
            justify=tk.RIGHT,
            textvariable=self._var_label,
        )
        self._var_entry = tk.StringVar(value='')
        self._entry_text_buffer: str = ''
        self._hidden_text_buffer: str = ''
        self.entry = ttk.Entry(
            master,
            justify=tk.LEFT,
            textvariable=self._var_entry,
            width=self.entry_width,
        )

        self.hide_button: ttk.Button | None = None
        self._is_hidden = False
        self._hide_default = False
        self.block_button: ttk.Button | None = None
        self._block_default = False
        self._is_blocked = False

    def grid(self):
        i = self.index
        pad = 5
        self.label.grid(column=0, row=i, sticky=tk.E, padx=pad, pady=pad)
        self.entry.grid(column=1, row=i, sticky=tk.W, padx=pad, pady=pad)
        if self.hide_button:
            self.hide_button.grid(column=2, row=i, sticky=tk.N, padx=pad, pady=pad)
        if self.block_button:
            self.block_button.grid(column=3, row=i, sticky=tk.N, padx=pad, pady=pad)

    def is_hidded(self) -> bool:
        if self.hide_button is None:
            return False
        return self._is_hidden

    def is_blocked(self) -> bool:
        if self.block_button is None:
            return False
        return self._is_blocked

    def set_label(self, text: str):
        self._var_label.set(text)

    def set_value(self, text: str):
        self._entry_text_buffer = text
        self._hidden_text_buffer = '*' * len(text)
        self._var_entry.set(text)

    def hide_input(self, event: tk.Event | None = None):
        self._var_entry.set(self._hidden_text_buffer)
        self._is_hidden = True
        if self.hide_button is not None:
            self.hide_button.config(text='!hide')

    def show_input(self, event: tk.Event | None = None):
        self._var_entry.set(self._entry_text_buffer)
        self._is_hidden = False
        if self.hide_button is not None:
            self.hide_button.config(text='hide')

    def add_hide_button(self, default: bool):
        self._hide_default = default
        self._is_hidden = self._hide_default
        state = tk.NORMAL if self._hide_default else tk.DISABLED
        self.hide_button = ttk.Button(
            self.master,
            state=state,
            default=state,
            takefocus=tk.FALSE,
        )
        self.hide_button.bind('<Button-1>', self.show_input)
        self.hide_button.bind('<ButtonRelease-1>', self.hide_input)
        if self._hide_default:
            self.hide_input()
        else:
            self.show_input()

    def toggle_blocked(self, event: tk.Event | None = None):
        if self._is_blocked:
            self.unblock_input()
        else:
            self.block_input()

    def add_block_input_button(self, default: bool):
        self._block_default = default
        self._is_blocked = self._block_default
        state = tk.NORMAL if self._block_default else tk.DISABLED
        self.block_button = ttk.Button(
            self.master,
            state=state,
            default=state,
            takefocus=False,
        )
        self.block_button.bind('<Button-1>', self.toggle_blocked)
        if self._block_default:
            self.block_input()
        else:
            self.unblock_input()

    def block_input(self, event: tk.Event | None = None):
        self.entry.config(state=tk.DISABLED)
        self._is_blocked = True
        if self.block_button is not None:
            self.block_button.config(text='!block')

    def unblock_input(self, event: tk.Event | None = None):
        self.entry.config(state=tk.NORMAL)
        self._is_blocked = False
        if self.block_button is not None:
            self.block_button.config(text='block')


class CertificateForm(CommonBase, ttk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.create_widgets()

    def pack(self):
        super().pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

    def create_widgets(self):
        self.created = FormEntry(self, 'Data Adicionado:')
        self.created.block_input()
        self.last_modified = FormEntry(self, 'Data Modificado:')
        self.last_modified.block_input()
        self.browsercontext_id = FormEntry(self, '')
        self.browsercontext_id.block_input()
        self.origin = FormEntry(self, 'Origem:')
        self.origin.add_block_input_button(default=True)
        self.cert_path = FormEntry(self, 'Arquivo de Certificado:')
        self.cert_path.add_block_input_button(default=True)
        self.key_path = FormEntry(self, 'Arquivo de Chave:')
        self.key_path.add_block_input_button(default=True)
        self.pfx_path = FormEntry(self, 'Arquivo de Certificado PFX:')
        self.pfx_path.add_block_input_button(default=True)
        self.passphrase = FormEntry(self, 'Senha:')
        self.passphrase.add_block_input_button(default=True)
        self.passphrase.add_hide_button(default=True)
        for entry in FormEntry.entries:
            entry.grid()


class CertificateManager(View):
    def __init__(self, master):
        super().__init__(master)
        self.title = Title(self)
        self.tree_frame = TreeFrame(self)
        self.tree = self.tree_frame.tree
        self.button = ButtonFrame(self)
        self.form = CertificateForm(self)
        self.pack_in_order()

    def pack_in_order(self):
        """Packs widgets in the strict order in which they need to."""
        self.title.pack()
        self.tree_frame.pack()
        self.button.pack()
        self.form.pack()
