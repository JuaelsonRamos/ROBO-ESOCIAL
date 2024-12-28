from __future__ import annotations

from src.bootstrap import Directory
from src.db.tables import ClientCertificate, ClientCertificateDict, ClientConfig
from src.exc import Tkinter
from src.gui.lock import TkinterLock
from src.gui.utils.units import padding
from src.gui.views.View import View
from src.windows import open_file_dialog

import math
import string
import tkinter as tk
import functools
import tkinter.ttk as ttk

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, Sequence

import tksvg

from sqlalchemy import Row


_common_padding: Final[int] = 5


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
    btn_submit: ActionButton
    btn_cancel: ActionButton


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

    def assign_buttons_events(self):
        global _widgets
        _edit_item = functools.partial(_widgets.form.event_generate, '<<EditItem>>')
        _delete_item = functools.partial(_widgets.form.event_generate, '<<DeleteItem>>')
        _reload_tree = functools.partial(_widgets.tree.event_generate, '<<ReloadTree>>')
        self.add.set_command(self._add_item_event)
        self.delete.set_command(_delete_item)
        self.edit.set_command(_edit_item)
        self.reload.set_command(_reload_tree)

    def _add_item_event(self, event: tk.Event | None = None):
        global _widgets
        # TODO: add way of defining order of event execution independent of widget tree
        # hierarchy. Currently, the deeper a widget is -- as in, it's inside one which
        # is inside another and another, etc -- the later it is scheduled to be executed.
        # NOTE: Maybe override Widget.bind() to map {sequence: callback} globally and
        # with a context manager like events_in_order(), have an override of
        # Widget.event_generate() append to a queue that runs in order upon context exit.
        # NOTE: This is nuts. Perhaps just assign every event to a global map and use it
        # instead of Widget.event_generate(). It'd be way better to pass state through it,
        # but I'd have to pay extra attention to the custom mainloop. Oh well...
        _widgets.tree.event_generate('<<ClearSelection>>')
        self.update()
        _widgets.form.event_generate('<<AddItem>>')


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

    class EventState:
        FocusItem = 1000

    def _define_headings(self):
        self.heading('index', text='#', anchor=tk.CENTER)
        self.column('index', anchor=tk.CENTER, minwidth=32, width=32)

        self.heading('created', text='Data de Criação', anchor=tk.CENTER)
        self.column('created', anchor=tk.CENTER, minwidth=125, width=150)

        self.heading('last_modified', text='Data Ultima Modificação', anchor=tk.CENTER)
        self.column('last_modified', anchor=tk.CENTER, minwidth=125, width=150)

        self.heading('origin', text='URL', anchor=tk.W)
        self.column('origin', anchor=tk.W, minwidth=150, width=250)

        self.heading('type', text='Tipo', anchor=tk.CENTER)
        self.column('type', anchor=tk.CENTER, minwidth=50, width=60)

        self.heading(
            'has_public_key', text='Chave Pública Registrada', anchor=tk.CENTER
        )
        self.column('has_public_key', anchor=tk.CENTER, minwidth=160, width=160)

        self.heading('has_passphrase', text='Senha Registrada', anchor=tk.CENTER)
        self.column('has_passphrase', anchor=tk.CENTER, minwidth=160, width=160)

    def _make_item_tree_data(
        self, cert: Row[tuple[ClientCertificate]]
    ) -> tuple[str, ...]:
        _id = str(cert._id)
        if cert.pfx is not None:
            _type = 'PFX'
        else:
            _type = Path(cert.cert_path).suffix.strip('.').upper()
        has_public_key = 'Sim' if cert.key is not None else 'Não'
        has_passphrase = 'Sim' if cert.passphrase is not None else 'Não'
        last_modified = ''
        if cert.last_modified is not None:
            last_modified = cert.last_modified.strftime(FormEntry.datetime_format)

        return (
            _id,
            cert.created.strftime(FormEntry.datetime_format),
            last_modified,
            cert.origin or '',
            _type,
            has_public_key,
            has_passphrase,
        )

    def reload(self, event: tk.Event):
        count = ClientCertificate.sync_count()
        if count == 0:
            return
        certs = ClientCertificate.sync_select_all_columns(
            '_id',
            'created',
            'last_modified',
            'origin',
            'pfx',
            'cert_path',
            'key',
            'passphrase',
        )
        for cert in certs:
            iid = str(cert._id)
            if self.exists(iid):
                self.item(iid, values=self._make_item_tree_data(cert))
                continue
            i = cert._id
            self.insert('', i, iid, values=self._make_item_tree_data(cert))
        # if a state is provided, treat it as an iid to be selected after reload
        if event.state != self.EventState.FocusItem:
            return
        focus_iid: int | str = event.x
        if focus_iid < 0:
            raise Tkinter.EventStateError('treeview iid is less than zero')
        focus_iid = str(focus_iid)
        self.focus(focus_iid)
        self.selection_set(focus_iid)

    def delete_focused(self, event: tk.Event):
        selection = self.selection()
        if len(selection) == 0:
            return
        ids = tuple(int(iid) for iid in selection)
        ClientCertificate.sync_delete_many_from_id(*ids)
        self.delete(*selection)

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
        self.bind('<<TreeviewSelect>>', self._check_selection, '+')
        self.bind('<Visibility>', self.reload)
        self.bind('<<ReloadTree>>', self.reload)
        self.bind('<Button-1>', self._check_clear_selection)
        self.bind('<<ClearSelection>>', self.clear_selection)

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

    def _check_selection(self, event: tk.Event | None = None):
        global _widgets
        iid: str | int = self.focus()
        if iid == '':
            _widgets.form.event_generate('<<ResetForm>>')
            return
        _widgets.form.event_generate('<<PreviewItem>>', state=iid)

    def _check_clear_selection(self, event: tk.Event):
        # widget element clicked, .e.g. 'heading', 'tree', 'cell', 'nothing'
        thing_clicked: str = self.identify_region(event.x, event.y)
        if thing_clicked not in ('nothing', 'heading'):
            return
        self.event_generate('<<ClearSelection>>')

    def clear_selection(self, event: tk.Event | None = None):
        selection: tuple[str | int, ...] = self.selection()
        if len(selection) == 0:
            # mouse event won't know whether an item is already selected
            return
        self.focus('')
        # triggers selection check which will clear form if none is selected
        self.selection_remove(selection)


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


class FormEntry(ttk.Frame):
    entries: list[FormEntry] = []
    label_width: int = 25
    entry_width: int = 35
    pad: int = 5
    datetime_format = '%d/%m/%Y %H:%M'
    date_format = '%d/%m/%Y'
    time_format = '%H:%M'
    _btn_svg_opts = {'width': 24, 'height': 24}
    _block_input_img_locked: tksvg.SvgImage | None = None
    _block_input_img_unlocked: tksvg.SvgImage | None = None
    _hide_input_img_hidden: tksvg.SvgImage | None = None
    _hide_input_img_shown: tksvg.SvgImage | None = None
    max_label_char_count: int = 0

    def __init__(
        self,
        master: CertificateForm,
        label_text: str | None = None,
    ):
        super().__init__(master, takefocus=tk.FALSE)
        self.index = len(self.entries)
        self.entries.append(self)
        self.entry: ttk.Entry
        self._var_label = tk.StringVar()
        self.label = ttk.Label(
            self,
            anchor=tk.E,
            justify=tk.RIGHT,
            textvariable=self._var_label,
        )
        self.set_label(label_text or 'Static Data Field:')
        self._var_entry = tk.StringVar(value='')
        self._entry_text_buffer: str = ''
        self.hide_button: ttk.Button | None = None
        self._is_hidden = False
        self._hide_default = False
        self.block_button: ttk.Button | None = None
        self._block_default = False
        self._is_blocked = False

        self.create_widgets()

    @abstractmethod
    def create_widgets(self): ...

    @classmethod
    def pack_all_entries(cls):
        for entry in cls.entries:
            entry.pack()
            if entry.index > 0:
                previous_entry = cls.entries[entry.index - 1]
                entry.pack_configure(after=previous_entry)

    def pack(self):
        super().pack(side=tk.TOP, fill=tk.X, padx=self.pad, pady=self.pad)
        self.label.pack(side=tk.LEFT, padx=self.pad)
        if self.block_button:
            self.block_button.pack(side=tk.RIGHT)
        if self.hide_button:
            self.hide_button.pack(side=tk.RIGHT, padx=self.pad)
        if self.hide_button and self.block_button:
            # side=tk.RIGHT positions in reverse order; after == before and vice versa
            self.hide_button.pack_configure(after=self.block_button)

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
        if (new_width := len(text)) > FormEntry.max_label_char_count:
            FormEntry.max_label_char_count = new_width
            for entry in self.entries:
                entry.label.config(width=new_width)
        self.label.config(width=FormEntry.max_label_char_count)

    def set_value(self, text: str):
        self._entry_text_buffer = text
        if text != '' and self._is_hidden:
            self._var_entry.set('*' * len(self._entry_text_buffer))
            return
        self._var_entry.set(text)

    def get_value(self) -> str:
        return self._entry_text_buffer

    def hide_input(self, event: tk.Event | None = None):
        self._var_entry.set('*' * len(self._entry_text_buffer))
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
        self.hide_button = ttk.Button(
            self,
            takefocus=tk.FALSE,
            padding=0,
        )
        if self._hide_input_img_hidden is None:
            self._hide_input_img_hidden = tksvg.SvgImage(
                file=Directory.ASSETS / 'eye-closed.svg',
                **self._btn_svg_opts,
            )
        if self._hide_input_img_shown is None:
            self._hide_input_img_shown = tksvg.SvgImage(
                file=Directory.ASSETS / 'eye.svg',
                **self._btn_svg_opts,
            )
        self.reset_hidden_state()

    def toggle_blocked(self, event: tk.Event | None = None):
        if self._is_blocked:
            self.unblock_input()
        else:
            self.block_input()

    def add_block_input_button(self, default: bool):
        self._block_default = default
        self._is_blocked = self._block_default
        state = tk.DISABLED if self._block_default else tk.NORMAL
        self.block_button = ttk.Button(
            self,
            state=state,
            takefocus=False,
            padding=0,
        )
        if self._block_input_img_locked is None:
            self._block_input_img_locked = tksvg.SvgImage(
                file=Directory.ASSETS / 'lock.svg',
                **self._btn_svg_opts,
            )
        if self._block_input_img_unlocked is None:
            self._block_input_img_unlocked = tksvg.SvgImage(
                file=Directory.ASSETS / 'lock-slash.svg',
                **self._btn_svg_opts,
            )
        self.reset_blocked_state()

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
            if self._block_input_img_locked is None:
                self.block_button.config(text='block')
            else:
                self.block_button.config(image=self._block_input_img_locked)

    def reset_blocked_state(self, event: tk.Event | None = None):
        if self._block_default:
            self.block_input()
        else:
            self.unblock_input()

    def reset_hidden_state(self, event: tk.Event | None = None):
        if self._hide_default:
            self.hide_input()
        else:
            self.show_input()

    def _assign_btn_events(self):
        # this function will override events
        if self.hide_button is not None:
            self.hide_button.bind('<Button-1>', self.show_input)
            self.hide_button.bind('<ButtonRelease-1>', self.hide_input)
        if self.block_button is not None:
            self.block_button.bind('<Button-1>', self.toggle_blocked)

    def _unbind_btn_events(self):
        if self.hide_button is not None:
            self.hide_button.unbind('<Button-1>')
            self.hide_button.unbind('<ButtonRelease-1>')
        if self.block_button is not None:
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
        if self.block_button is not None:
            self.reset_blocked_state()
            self.block_button.config(state=tk.NORMAL)
        if self.hide_button is not None:
            self.reset_hidden_state()
            self.hide_button.config(state=tk.NORMAL)
        self.label.config(state=tk.NORMAL)


class TextEntry(FormEntry):
    def create_widgets(self):
        tcl_callback = self.register(self._check_is_hidden)
        self.entry = ttk.Entry(
            self,
            justify=tk.LEFT,
            textvariable=self._var_entry,
            width=self.entry_width,
            validate='key',
            validatecommand=(tcl_callback, '%d', '%S', '%i'),
        )

    def _check_is_hidden(self, action: int, text: str, index: str) -> bool:
        # not insertion nor deletion
        if action == '-1':
            return False
        if text == '':
            return True
        i = int(index)
        if action == '0':
            # deletion
            if self._entry_text_buffer == '':
                # noop
                self.set_value('')
                self.entry.icursor(0)
            elif i == 0:
                # delete prefix
                self.set_value(self._entry_text_buffer.removeprefix(text))
                self.entry.icursor(0)
            elif i == len(self._entry_text_buffer) - len(text):
                # delete suffix
                self.set_value(self._entry_text_buffer.removesuffix(text))
                self.entry.icursor(len(self._entry_text_buffer))
            else:
                # delete in the middle
                left_side = self._entry_text_buffer[:i]
                right_side = self._entry_text_buffer[i + len(text) :]
                self.set_value(left_side + right_side)
                self.entry.icursor(len(left_side))
        elif action == '1':
            # insertion
            if self._entry_text_buffer == '' or i == 0:
                # insert prefix
                self.set_value(text + self._entry_text_buffer)
                self.entry.icursor(len(text))
            elif i == len(self._entry_text_buffer):
                # insert suffix
                self.set_value(self._entry_text_buffer + text)
                self.entry.icursor(len(self._entry_text_buffer))
            else:
                # insert in the middle
                left_side = self._entry_text_buffer[:i]
                right_side = self._entry_text_buffer[i:]
                self.set_value(left_side + text + right_side)
                self.entry.icursor(i + len(text))
        return True

    def pack(self):
        super().pack()
        self.entry.pack(side=tk.LEFT, padx=self.pad, fill=tk.X)


class FileEntry(TextEntry):
    _open_file_img: tksvg.SvgImage

    def __init__(self, master, label_text, extensions: Sequence[tuple]):
        self._open_file_img = tksvg.SvgImage(
            file=Directory.ASSETS / 'submit-document.svg', **self._btn_svg_opts
        )
        self._filedialog_options = extensions
        super().__init__(master, label_text)

    def create_widgets(self):
        self.sub_frame = ttk.Frame(self, takefocus=tk.FALSE)
        self.open = ttk.Button(
            self.sub_frame,
            takefocus=tk.TRUE,
            command=self.open_file,
            image=self._open_file_img,
        )
        self.entry = ttk.Entry(self.sub_frame, justify=tk.LEFT, width=self.entry_width)

    def _insert_path(self, value: str | Exception, raised: bool) -> None:
        if raised:
            raise value  # type: ignore
        self.set_value(value)  # type: ignore

    def open_file(self):
        _callback = functools.partial(
            open_file_dialog,
            hwnd=self.winfo_id(),
            title='Selecionar arquivo (Certificado Digital)',
            extensions=self._filedialog_options,
            multi_select=False,
        )
        lock = TkinterLock
        lock.schedule(self, _callback, self._insert_path, block=False)

    def pack(self):
        super().pack()  # packs entry
        self.sub_frame.pack(side=tk.LEFT, fill=tk.X, after=self.label)
        self.open.pack(side=tk.LEFT, after=self.entry)

    def block_input(self, event: tk.Event | None = None):
        super().block_input(event)
        self.open.config(state=tk.DISABLED)

    def unblock_input(self, event: tk.Event | None = None):
        super().unblock_input(event)
        self.open.config(state=tk.NORMAL)


class CertificateForm(ttk.Frame):
    autofill_message = '(Preenchimento automático)'

    def __init__(self, master: CertificateManager):
        super().__init__(master)
        self.parent_widget = master
        self.create_widgets()

    def pack(self):
        super().pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        FormEntry.pack_all_entries()
        self.btn_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        self.btn_submit.pack(side=tk.RIGHT)
        self.btn_cancel.pack(side=tk.RIGHT, before=self.btn_submit)

    def create_widgets(self):
        self.created = TextEntry(self, 'Data Adicionado:')
        self.created.block_input()
        self.last_modified = TextEntry(self, 'Data Modificado:')
        self.last_modified.block_input()
        self.browsercontext_id = TextEntry(self, 'Contexto de navegador:')
        self.browsercontext_id.block_input()
        self.description = TextEntry(self, 'Descrição:')
        self.description.unblock_input()
        self.origin = TextEntry(self, 'Origem:')
        self.origin.add_block_input_button(default=True)
        self.cert_path = FileEntry(
            self, 'Arquivo de Certificado:', [('Certificado PFX (*.pfx)', ('*.pfx',))]
        )
        self.cert_path.add_block_input_button(default=True)
        self.key_path = FileEntry(
            self,
            'Arquivo de Chave:',
            [('Certificado Digital (*.crt;*.pem)', ('*.crt', '*.pem'))],
        )
        self.key_path.add_block_input_button(default=True)
        self.pfx_path = FileEntry(
            self, 'Arquivo de Certificado PFX:', [('Chave de Certificado (*)', ('*',))]
        )
        self.pfx_path.add_block_input_button(default=True)
        self.passphrase = TextEntry(self, 'Senha:')
        self.passphrase.add_block_input_button(default=True)
        self.passphrase.add_hide_button(default=True)
        self.btn_frame = ttk.Frame(self)
        self.btn_submit = ActionButton(self.btn_frame, 'Confirmar')
        self.btn_cancel = ActionButton(
            self.btn_frame, 'Cancelar', command=self.reset_form
        )

    def assign_form_events(self):
        self.bind('<<AddItem>>', self.prepare_add_item)
        self.bind('<<EditItem>>', self.prepare_edit_item)
        self.bind('<<DeleteItem>>', self.prepare_delete_item)
        self.bind('<<ResetForm>>', self.reset_form)
        self.bind('<<PreviewItem>>', self._preview_item_event)

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
        cert = ClientCertificate.sync_select_one_from_id(_id)
        if cert is None:
            raise ValueError('cert does not exist')
        data = ClientCertificateDict(**cert._asdict())
        if 'created' in data:
            self.created.set_value(data['created'].strftime(FormEntry.datetime_format))
        else:
            self.created.set_value(self.autofill_message)
        if 'last_modified' in data and (value := data['last_modified']) is not None:
            self.last_modified.set_value(value.strftime(FormEntry.datetime_format))
        else:
            self.last_modified.set_value(self.autofill_message)
        if (
            'browsercontext_id' in data
            and (value := data['browsercontext_id']) is not None
        ):
            self.browsercontext_id.set_value(str(value))
        else:
            self.browsercontext_id.set_value(self.autofill_message)
        if 'key_path' in data and (value := data['key_path']) is not None:
            self.key_path.set_value(value.decode())
        else:
            self.key_path.set_value('')
        self.description.set_value(data.get('description', None) or '')
        self.origin.set_value(data.get('origin', None) or '')
        self.cert_path.set_value(data.get('cert_path', None) or '')
        self.pfx_path.set_value(data.get('pfx_path', None) or '')
        self.passphrase.set_value(data.get('passphrase', None) or '')

    def reset_form(self, event: tk.Event | None = None):
        for entry in FormEntry.entries:
            entry.set_value('')
        self.btn_cancel.set_command('')
        self.btn_submit.set_command('')
        self.block_all_form_interactions()

    def _preview_item_event(self, event: tk.Event):
        iid: int | str = event.state
        _id: int = iid if isinstance(iid, int) else int(iid)
        self.fill_form_by_db_id(_id)

    def prepare_add_item(self, event: tk.Event | None = None):
        self.allow_form_interactions()
        self.btn_submit.set_command(self.insert_from_form_fields)
        self.created.set_value(self.autofill_message)
        self.created.block_input()
        self.last_modified.set_value(self.autofill_message)
        self.last_modified.block_input()
        self.browsercontext_id.set_value(self.autofill_message)
        self.browsercontext_id.block_input()
        self.description.set_value('')
        self.description.unblock_input()
        self.origin.set_value('')
        self.origin.unblock_input()
        self.cert_path.set_value('')
        self.cert_path.unblock_input()
        self.key_path.set_value('')
        self.key_path.unblock_input()
        self.pfx_path.set_value('')
        self.pfx_path.unblock_input()
        self.passphrase.set_value('')
        self.passphrase.unblock_input()
        self.passphrase.hide_input()

    def prepare_edit_item(self, event: tk.Event | None = None):
        global _widgets
        iid = _widgets.tree.focus()
        if iid == '':
            return
        _id = int(iid)
        self.allow_form_interactions()
        self.fill_form_by_db_id(_id)
        self.btn_submit.set_command(self.update_from_form_fields)
        self.created.block_input()
        self.last_modified.block_input()
        self.browsercontext_id.block_input()
        self.description.unblock_input()
        self.origin.unblock_input()
        self.cert_path.unblock_input()
        self.key_path.unblock_input()
        self.pfx_path.unblock_input()
        self.passphrase.unblock_input()
        self.passphrase.hide_input()

    def prepare_delete_item(self, event: tk.Event | None = None):
        global _widgets
        iid = _widgets.tree.focus()
        if iid == '':
            return
        _id = int(iid)
        self.allow_form_interactions()
        self.fill_form_by_db_id(_id)
        for entry in FormEntry.entries:
            entry.block_input()
            if entry.block_button is not None:
                entry.block_button.config(state=tk.DISABLED)
            if entry.hide_button is not None:
                entry.hide_button.config(state=tk.NORMAL)
        self.btn_submit.set_command(self.delete_from_form_fields)

    def form_db_row_data(self) -> ClientCertificateDict:
        origin = self.origin.get_value().strip(string.whitespace)
        description = self.description.get_value().strip(string.whitespace)
        passphrase: str | None = self.passphrase.get_value().strip(string.whitespace)
        if passphrase == '':
            passphrase = None
        cert_path: str = self.cert_path.get_value().strip(string.whitespace)
        key_path: str = self.key_path.get_value().strip(string.whitespace)
        pfx_path: str = self.pfx_path.get_value().strip(string.whitespace)

        max_bytes = ClientConfig.SQLITE_LIMIT_LENGTH

        def size_error(p):
            return ValueError(f'file {p=} is bigger than {max_bytes=}')

        data = ClientCertificateDict(
            origin=origin,
            cert_path=None,
            cert=None,
            key_path=None,
            key=None,
            pfx_path=None,
            pfx=None,
            passphrase=passphrase or None,
            # TODO: implement gui cert type selection
            using_type='PFX',
            description=description,
        )

        if cert_path != '' and (p := Path(cert_path)).is_file():
            if p.stat().st_size > max_bytes:
                raise size_error(p)
            data.update(cert_path=str(p.absolute()), cert=p.read_bytes())
        if key_path != '' and (p := Path(key_path)).is_file():
            if p.stat().st_size > max_bytes:
                raise size_error(p)
            data.update(key_path=str(p.absolute()).encode(), key=p.read_bytes())
        if pfx_path != '' and (p := Path(pfx_path)).is_file():
            if p.stat().st_size > max_bytes:
                raise size_error(p)
            data.update(pfx_path=str(p.absolute()), pfx=p.read_bytes())

        return data

    def insert_from_form_fields(self):
        data = self.form_db_row_data()
        inserted_id: int = ClientCertificate.sync_insert_one(data)
        global _widgets
        _widgets.tree.event_generate(
            '<<ReloadTree>>',
            state=_widgets.tree.EventState.FocusItem,
            x=inserted_id,
        )

    def delete_from_form_fields(self):
        global _widgets
        iid = _widgets.tree.focus()
        if iid == '':
            raise ValueError('empty iid')
        _id = int(iid)
        ClientCertificate.sync_delete_one_from_id(_id)

    def update_from_form_fields(self):
        global _widgets
        data = self.form_db_row_data()
        iid = _widgets.tree.focus()
        if iid == '':
            raise ValueError('empty iid')
        _id = int(iid)
        ClientCertificate.sync_update_one_from_id(data, _id)


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
            self.form.btn_submit,
            self.form.btn_cancel,
        )

        self.pack_in_order()
        self.tree_frame.assign_layout_events()
        self.tree.assign_tree_events()
        self.buttons_frame.assign_buttons_events()
        self.form.assign_form_events()
        self.tree.init_tree_state()

    def pack_in_order(self):
        """Packs widgets in the strict order in which they need to."""
        self.title.pack()
        self.tree_frame.pack()
        self.buttons_frame.pack()
        self.buttons_frame.pack_configure(after=self.title)
        self.form.pack()
