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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tkinter import scrolledtext
from typing import Final, Literal, Sequence, cast

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
    btn_update: ActionButton


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
    # TODO

    def __init__(self, master: ButtonFrame):
        super().__init__(master)
        self.parent_widget = master


class ButtonFrame(ttk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.parent_widget = master

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
        # prevents column resizing
        # SEE https://stackoverflow.com/a/71710427/15493645
        self.bind('<Motion>', 'break')
        self._define_headings()
        self.bind('<<TreeviewSelect>>', self._update_select)
        self.bind('<<ReloadTree>>', self.reload)
        self.bind('<<DeleteItem>>', self.delete_focused)
        self.bind('<<AddItem>>', self.add_item)

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


class ScrollableCanvas(tk.Canvas):
    # TODO

    def __init__(self, master: TreeFrame):
        super().__init__(master)
        self.parent_widget = master


class TreeFrame(tk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.parent_widget = master
        self.scrolling_canvas = tk.Canvas(self)
        self.tree = CertificateList(self.scrolling_canvas)  # type: ignore
        self.tree_window = self.scrolling_canvas.create_window(
            0, 0, anchor=tk.NW, window=self.tree
        )

        self.scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.scroll.config(command=self.scrolling_canvas.xview)
        self.scrolling_canvas.config(xscrollcommand=self.scroll.set)

        self.scrolling_canvas.bind('<Visibility>', self.resize)
        self.scrolling_canvas.bind('<MouseWheel>', self._scroll_mousewheel)
        self.scroll.bind('<MouseWheel>', self._scroll_mousewheel)
        self.tree.bind('<MouseWheel>', self._scroll_mousewheel)

    def xview(
        self,
        kind: Literal['moveto', 'scroll'],
        delta: float | str,
        unit: Literal['units', 'pages'] | None = None,
    ):
        """Moves tree by given float factor. Method compatible with .xview() on canvas, treeview, etc."""
        if kind != tk.MOVETO:
            return
        tree_x = self.tree.winfo_x()
        tree_width = self.tree.winfo_reqwidth()
        frame_width = self.get_width()
        if isinstance(delta, str):
            delta = float(delta)
        current = self.scroll.get()
        is_moving_left: bool = abs(delta) < 0.5
        is_moving_right: bool = abs(delta) > 0.5
        # negative factor == left, positive factor == right
        factor_movement: float = 0
        pixels_moved: int = 0
        start: int = 0
        if delta != 0:
            if is_moving_left:
                factor_movement = 0.5 * abs(delta)
            else:
                factor_movement = 0.5 * (abs(delta) - 0.5)
            pixels_moved = math.ceil(frame_width * factor_movement)
            if is_moving_right:
                # scrollbar goes to the right, x decreases
                start = tree_x - pixels_moved
            elif is_moving_left:
                # scrollbar goes to the left, x increases
                start = tree_x + pixels_moved
            else:
                start = 0
            if abs(start) + frame_width >= tree_width:
                # would overflow
                if start < 0:
                    # prevent crop to the right
                    start = -(tree_width - frame_width)
                else:
                    # prevent crop to the left
                    start = 0
        self._tree_relative_x = start
        frame_x = self.winfo_rootx()
        self._tree_absolute_x = frame_x + start  # if start < 0, adding will subtract
        self.tree.place(x=self._tree_relative_x)
        scroll_start: float = abs(start) / tree_width
        scroll_end: float = (abs(start) + frame_width) / tree_width
        self.scroll.set(scroll_start, scroll_end)

    def _scroll_mousewheel(self, event: tk.Event):
        # 1 mouse scroll == 120 on windows, so the wheel's step is 120 at a time
        acceleration = 1
        scroll_length = event.delta // 120
        if scroll_length < 0:
            scroll_length -= acceleration
        else:
            scroll_length += acceleration
        self.scrolling_canvas.xview_scroll(scroll_length, tk.UNITS)

    def scroll_frame(self, delta: float):
        self.xview(tk.MOVETO, delta)

    def _init_scrollbar(self, event: tk.Event | None):
        self.scroll_frame(0)
        self.tree.unbind('<Visibility>', self._init_scrollbar)  # type: ignore

    def get_width(self):
        window_size = self.master.winfo_width()
        return math.ceil(window_size * 0.5)

    def resize(self, event: tk.Event | None = None):
        frame_width = self.get_width()
        tree_width = self.tree.winfo_reqwidth()
        canvas_height = self.scrolling_canvas.winfo_height()
        self.config(width=frame_width)
        self.scrolling_canvas.config(
            width=frame_width,
            scrollregion=(0, 0, tree_width, 0),
        )
        self.scrolling_canvas.itemconfig(
            self.tree_window,
            height=canvas_height,
        )

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


class CertificateForm(ttk.Frame):
    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.parent_widget = master
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
