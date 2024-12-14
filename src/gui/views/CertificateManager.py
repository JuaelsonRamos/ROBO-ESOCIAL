from __future__ import annotations

from src import bootstrap
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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tkinter import scrolledtext
from typing import Callable, Final, Literal, Sequence, cast, overload

import tksvg

from sqlalchemy import func


_common_padding: Final[int] = 5

dirs = bootstrap.Directory()


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

    def get_one(self, _id: int) -> ClientCertificate | None:
        with self.engine.begin() as conn:
            query = self.table.select().where(ClientCertificate._id == _id)
            return conn.scalar(query)


db_helpers = DatabaseHelper()


@dataclass(frozen=False, slots=True)
class WidgetsNamespace:
    title: Title
    buttons_frame: ButtonFrame
    form: CertificateForm
    tree: CertificateList
    tree_frame: TreeFrame
    tree_canvas: ScrollableCanvas
    btn_add: ActionButton
    btn_edit: ActionButton
    btn_delete: ActionButton
    btn_reload: ActionButton


# should be assigned on root instanciation
_widgets: WidgetsNamespace = None  # type: ignore


class Title(ttk.Label):
    def __init__(self, master: CertificateManager):
        super().__init__(
            master, anchor=tk.CENTER, justify=tk.CENTER, text='Certificados'
        )
        self.parent_widget = master

    def pack(self):
        super().pack(
            side=tk.TOP, fill=tk.X, ipady=_common_padding * 2, anchor=tk.CENTER
        )


class ActionButton(ttk.Button):
    def __init__(
        self,
        master: ttk.Widget,
        text: str = 'ActionButton',
        command: str | Callable = '',
    ) -> None:
        super().__init__(
            master,
            width=15,
            padding=padding(left=5, right=5),
            text=text,
            command=command,
        )
        self.parent_widget = master
        self.tk_callback = command

    def set_command(self, command: str | Callable):
        self.tk_callback = command
        self.config(command=command)

    def disable(self):
        self.config(state=tk.DISABLED)

    def active(self):
        self.config(state=tk.NORMAL)


class ButtonFrame(ttk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.parent_widget = master
        self.add = ActionButton(self, text='Adicionar')
        self.delete = ActionButton(self, text='Deletar')
        self.reload = ActionButton(self, text='Atualizar')
        self.edit = ActionButton(self, text='Editar')

    def pack(self):
        super().pack(side=tk.TOP, anchor=tk.CENTER, padx=5, pady=5)

        self.delete.pack(side=tk.LEFT)
        self.add.pack(side=tk.LEFT, before=self.delete)
        self.edit.pack(side=tk.LEFT, after=self.delete)
        self.reload.pack(side=tk.LEFT, after=self.edit)


class CertificateList(ttk.Treeview):
    def __init__(self, master: ScrollableCanvas):
        self.parent_widget = master
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
        self._define_headings()

    def _define_headings(self):
        self.heading('index', text='#', anchor=tk.CENTER)
        self.column('index', anchor=tk.CENTER, minwidth=32, width=32)

        self.heading('created', text='Data de Criação', anchor=tk.CENTER)
        self.column('created', anchor=tk.CENTER, minwidth=125, width=150)

        self.heading('last_modified', text='Data Ultima Modificação', anchor=tk.CENTER)
        self.column('last_modified', anchor=tk.CENTER, minwidth=125, width=150)

        self.heading('origin', text='URL', anchor=tk.W)
        self.column('origin', anchor=tk.CENTER, minwidth=150, width=250)

        self.heading('type', text='Tipo', anchor=tk.CENTER)
        self.column('type', anchor=tk.CENTER, minwidth=50, width=60)

        self.heading(
            'has_public_key', text='Chave Pública Registrada', anchor=tk.CENTER
        )
        self.column('has_public_key', anchor=tk.CENTER, minwidth=160, width=160)

        self.heading('has_passphrase', text='Senha Registrada', anchor=tk.CENTER)
        self.column('has_passphrase', anchor=tk.CENTER, minwidth=160, width=160)

    def get_certs(self) -> Sequence[Path]:
        certs = get_certificates()
        by_creation_time = sorted(certs, key=lambda path: path.stat().st_ctime)
        return by_creation_time

    def _make_item_tree_data(self, cert: ClientCertificate) -> tuple[str, ...]:
        _id = str(cert._id)
        if cert.pfx is not None:
            _type = 'PFX'
        else:
            _type = Path(cert.cert_path).suffix.strip('.').upper()
        has_public_key = 'Sim' if cert.key is not None else 'Não'
        has_passphrase = 'Sim' if cert.passphrase is not None else 'Não'

        return (
            _id,
            cert.created.strftime(FormEntry.datetime_format),
            cert.last_modified.strftime(FormEntry.datetime_format),
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

    def init_tree_state(self):
        global _widgets
        selected = self.selection()
        if len(selected) > 0:
            self.selection_remove(selected)
        _widgets.btn_delete.disable()
        _widgets.btn_edit.disable()
        _widgets.form.block_all_form_interactions()

    def assign_tree_events(self):
        global _widgets
        # prevents column resizing
        # SEE https://stackoverflow.com/a/71710427/15493645
        self.bind('<Motion>', 'break')
        self.bind('<<TreeviewSelect>>', self._toggle_btn_state)
        self.bind('<<ReloadTree>>', self.reload)
        self.bind('<<DeleteItem>>', self.delete_focused)
        self.bind('<<AddItem>>', self.add_item)
        _reload_tree = functools.partial(self.event_generate, '<<ReloadTree>>')
        _add_item = functools.partial(self.event_generate, '<<AddItem>>')
        _delete_item = functools.partial(self.event_generate, '<<DeleteItem>>')
        _widgets.btn_add.set_command(_add_item)
        _widgets.btn_delete.set_command(_delete_item)
        _widgets.btn_reload.set_command(_reload_tree)

    def _toggle_btn_state(self, event: tk.Event):
        global _widgets
        if self.focus() == '':
            _widgets.btn_delete.disable()
            _widgets.btn_edit.disable()
            _widgets.form.block_all_form_interactions()
            return
        _widgets.btn_delete.active()
        _widgets.btn_edit.active()
        _widgets.form.allow_form_interactions()


class ScrollableCanvas(tk.Canvas):
    def __init__(self, master: TreeFrame):
        super().__init__(master)
        self.parent_widget = master
        self.window_id = self.create_window(0, 0, anchor=tk.NW)
        self.window_widget: ttk.Widget | None = None

    def set_window(self, widget: ttk.Widget):
        self.itemconfig(self.window_id, window=widget)
        self.window_widget = widget

    def set_window_height(self, height: int):
        self.itemconfig(self.window_id, height=height)

    def set_canvas_size(self, width: int):
        self.config(width=width)
        if self.window_widget is not None:
            # scrollregion == tuple[int, ...] == (w, n, e, s)
            reqwidth = self.window_widget.winfo_reqwidth()
            self.config(scrollregion=(0, 0, reqwidth, 0))
            avail_height = self.winfo_height()
            self.itemconfig(self.window_id, height=avail_height)


class TreeFrame(tk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.parent_widget = master
        self.scrolling_canvas = ScrollableCanvas(self)
        self.tree = CertificateList(self.scrolling_canvas)  # type: ignore
        self.scrolling_canvas.set_window(self.tree)

        self.scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.scroll.config(command=self.scrolling_canvas.xview)
        self.scrolling_canvas.config(xscrollcommand=self.scroll.set)

    def assign_layout_events(self):
        self.scrolling_canvas.bind('<Visibility>', self.resize)
        self.scrolling_canvas.bind('<MouseWheel>', self._scroll_mousewheel)
        self.scroll.bind('<MouseWheel>', self._scroll_mousewheel)
        self.tree.bind('<MouseWheel>', self._scroll_mousewheel)

    def _scroll_mousewheel(self, event: tk.Event):
        # 1 mouse scroll == 120 on windows, so the wheel's step is 120 at a time
        acceleration = 1
        scroll_length = event.delta // 120
        if scroll_length < 0:
            scroll_length -= acceleration
        else:
            scroll_length += acceleration
        self.scrolling_canvas.xview_scroll(scroll_length, tk.UNITS)

    def resize(self, event: tk.Event | None = None):
        frame_width = math.ceil(self.parent_widget.winfo_width() * 0.5)
        self.config(width=frame_width)
        self.scrolling_canvas.set_canvas_size(frame_width)

    def pack(self):
        super().pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        self.pack_propagate(tk.FALSE)
        self.scrolling_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)
        self.scroll.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            after=self.scrolling_canvas,
        )


class FormEntry:
    _get_class_instance_number = itertools.count(0).__next__
    entries: list[FormEntry] = []
    label_width: int = 25
    entry_width: int = 35
    datetime_format = '%d/%m/%Y %H:%M'
    _btn_svg_opts = {'width': 24, 'height': 24}
    _block_input_img_locked: tksvg.SvgImage | None = None
    _block_input_img_unlocked: tksvg.SvgImage | None = None
    _hide_input_img_hidden: tksvg.SvgImage | None = None
    _hide_input_img_shown: tksvg.SvgImage | None = None

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
        self.master.grid_rowconfigure(i, minsize=35, pad=pad)
        self.label.grid(column=0, row=i, sticky=tk.E, padx=pad)
        self.entry.grid(column=1, row=i, sticky=tk.W, padx=pad)
        if self.hide_button:
            self.hide_button.grid(column=2, row=i, padx=pad)
        if self.block_button:
            self.block_button.grid(column=3, row=i)

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

    def get_value(self) -> str:
        return self._entry_text_buffer

    def hide_input(self, event: tk.Event | None = None):
        self._var_entry.set(self._hidden_text_buffer)
        self._is_hidden = True
        if self.hide_button is not None:
            # icon should indicate pressing it will show
            if self._hide_input_img_shown is None:
                self.hide_button.config(text='!hide')
            else:
                self.hide_button.config(image=self._hide_input_img_shown)

    def show_input(self, event: tk.Event | None = None):
        self._var_entry.set(self._entry_text_buffer)
        self._is_hidden = False
        if self.hide_button is not None:
            # icon should indicate releasing it will hide
            if self._hide_input_img_hidden is None:
                self.hide_button.config(text='hide')
            else:
                self.hide_button.config(image=self._hide_input_img_hidden)

    def add_hide_button(self, default: bool):
        self._hide_default = default
        self._is_hidden = self._hide_default
        state = tk.NORMAL if self._hide_default else tk.DISABLED
        self.hide_button = ttk.Button(
            self.master,
            state=state,
            default=state,
            takefocus=tk.FALSE,
            padding=0,
        )
        if self._hide_input_img_hidden is None:
            self._hide_input_img_hidden = tksvg.SvgImage(
                file=dirs.ASSETS / 'eye-closed.svg',
                **self._btn_svg_opts,
            )
        if self._hide_input_img_shown is None:
            self._hide_input_img_shown = tksvg.SvgImage(
                file=dirs.ASSETS / 'eye.svg',
                **self._btn_svg_opts,
            )
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
            padding=0,
        )
        if self._block_input_img_locked is None:
            self._block_input_img_locked = tksvg.SvgImage(
                file=dirs.ASSETS / 'lock.svg',
                **self._btn_svg_opts,
            )
        if self._block_input_img_unlocked is None:
            self._block_input_img_unlocked = tksvg.SvgImage(
                file=dirs.ASSETS / 'lock-slash.svg',
                **self._btn_svg_opts,
            )
        if self._block_default:
            self.block_input()
        else:
            self.unblock_input()

    def block_input(self, event: tk.Event | None = None):
        self.entry.config(state=tk.DISABLED)
        self._is_blocked = True
        if self.block_button is not None:
            # button icon should indicate pressing it will UNLOCK
            if self._block_input_img_unlocked is None:
                self.block_button.config(text='!block')
            else:
                self.block_button.config(image=self._block_input_img_unlocked)

    def unblock_input(self, event: tk.Event | None = None):
        self.entry.config(state=tk.NORMAL)
        self._is_blocked = False
        if self.block_button is not None:
            # button icon should indicate pressing it will LOCK
            if self._block_input_img_unlocked is None:
                self.block_button.config(text='block')
            else:
                self.block_button.config(image=self._block_input_img_unlocked)

    def _assign_btn_events(self):
        # this function will override events
        if self.hide_button is None or self.block_button is None:
            return
        self.hide_button.bind('<Button-1>', self.show_input)
        self.hide_button.bind('<ButtonRelease-1>', self.hide_input)
        self.block_button.bind('<Button-1>', self.toggle_blocked)

    def _unbind_btn_events(self):
        if self.hide_button is None or self.block_button is None:
            return
        self.hide_button.unbind('<Button-1>')
        self.hide_button.unbind('<ButtonRelease-1>')
        self.block_button.unbind('<Button-1>')

    def disable_all_interactions(self):
        self._unbind_btn_events()
        self.block_input()
        self.label.config(state=tk.DISABLED)
        if self.hide_button is not None:
            self.hide_button.config(state=tk.DISABLED)
        if self.block_button is not None:
            self.block_button.config(state=tk.DISABLED)

    def enable_all_interactions(self):
        self._assign_btn_events()
        self.label.config(state=tk.NORMAL)
        if self.entry.config('default') == tk.DISABLED:
            self.block_input()
        elif self.entry.config('default') == tk.NORMAL:
            self.unblock_input()
        if self.hide_button is not None:
            self.hide_button.config(state=tk.NORMAL)
        if self.block_button is not None:
            self.block_button.config(state=tk.NORMAL)


class CertificateForm(ttk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.parent_widget = master
        self.create_widgets()

    def pack(self):
        super().pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        for entry in FormEntry.entries:
            entry.grid()
        cols, rows = self.grid_size()  # values are equivalent to 1-based indexes
        self.btn_frame.grid(column=0, row=rows, columnspan=cols, pady=10, sticky=tk.EW)
        self.btn_submit.pack(side=tk.RIGHT)
        self.btn_cancel.pack(side=tk.RIGHT, before=self.btn_submit)

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
        self.btn_frame = ttk.Frame(self)
        self.btn_submit = ActionButton(self.btn_frame, 'Confirmar')
        self.btn_cancel = ActionButton(self.btn_frame, 'Cancelar')

    def block_all_form_interactions(self):
        for entry in FormEntry.entries:
            entry.disable_all_interactions()
        self.btn_submit.disable()
        self.btn_cancel.disable()

    def allow_form_interactions(self):
        for entry in FormEntry.entries:
            entry.enable_all_interactions()
        self.btn_submit.active()
        self.btn_cancel.active()

    def fill_form_by_db_id(self, _id: int):
        cert = db_helpers.get_one(_id)
        if cert is None:
            return
        self.created.set_value(cert.created.strftime(FormEntry.datetime_format))
        if cert.last_modified is not None:
            self.last_modified.set_value(
                cert.last_modified.strftime(FormEntry.datetime_format)
            )
        self.browsercontext_id.set_value(str(cert.browsercontext_id))
        self.origin.set_value(cert.origin)
        if cert.cert_path is not None:
            self.cert_path.set_value(cert.cert_path)
        if cert.key_path is not None:
            self.key_path.set_value(cert.key_path.decode())
        if cert.pfx_path is not None:
            self.pfx_path.set_value(cert.pfx_path)
        if cert.passphrase is not None:
            self.passphrase.set_value(cert.passphrase)

    def insert_from_form_fields(self):
        # TODO
        pass

    def delete_from_form_fields(self):
        # TODO
        pass

    def update_from_form_fields(self):
        # TODO
        pass


class CertificateManager(View):
    def __init__(self, master):
        super().__init__(master)
        self.title = Title(self)
        self.tree_frame = TreeFrame(self)
        self.tree = self.tree_frame.tree
        self.buttons_frame = ButtonFrame(self)
        self.form = CertificateForm(self)

        global _widgets
        _widgets = WidgetsNamespace(
            self.title,
            self.buttons_frame,
            self.form,
            self.tree_frame.tree,
            self.tree_frame,
            self.tree_frame.scrolling_canvas,
            self.buttons_frame.add,
            self.buttons_frame.edit,
            self.buttons_frame.delete,
            self.buttons_frame.reload,
        )

        self.pack_in_order()
        self.tree.assign_tree_events()
        self.tree.init_tree_state()
        self.tree_frame.assign_layout_events()

    def pack_in_order(self):
        """Packs widgets in the strict order in which they need to."""
        self.title.pack()
        self.tree_frame.pack()
        self.buttons_frame.pack()
        self.buttons_frame.pack_configure(after=self.title)
        self.form.pack()
