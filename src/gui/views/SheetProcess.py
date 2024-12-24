from __future__ import annotations

from src.db.tables import TkinterGlobal, Workbook, WorkbookDict, Worksheet
from src.exc import SheetParsing
from src.gui.lock import TkinterLock
from src.gui.utils.units import padding
from src.gui.views.View import View
from src.sistema.sheet import Sheet
from src.sistema.sheet_constants import SHEET_FILEDIALOG_OPTIONS
from src.windows import open_file_dialog

import re
import string
import tkinter as tk
import functools
import tkinter.ttk as ttk

from abc import abstractmethod
from pathlib import Path
from typing import Any, Never, TypedDict, cast, get_type_hints

from sqlalchemy import delete, func, select
from unidecode import unidecode_expect_nonascii as unidecode


re_whitespace = re.compile(f'[{string.whitespace}]+')


class Heading(TypedDict):
    text: str
    iid: str
    anchor: str
    width: int | None
    minwidth: int | None


HeadingSequence = tuple[Heading, ...]


INPUT_QUEUE: HeadingSequence = (
    {
        'text': '#',
        'iid': 'list_order',
        'anchor': tk.CENTER,
        'minwidth': 28,
        'width': 28,
    },
    {
        'text': 'Nome',
        'iid': 'file_name',
        'anchor': tk.W,
        'minwidth': 250,
        'width': 350,
    },
    {
        'text': 'Tipo',
        'iid': 'file_type',
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Tamanho',
        'iid': 'storage_size',
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Adicionado',
        'iid': 'date_added',
        'anchor': tk.CENTER,
        'minwidth': 150,
        'width': 180,
    },
)


HISTORY: HeadingSequence = (
    {
        'text': 'Ordem',
        'iid': 'list_order',
        'anchor': tk.E,
        'minwidth': 50,
        'width': 80,
    },
    {
        'text': 'Nome',
        'iid': 'file_name',
        'anchor': tk.W,
        'minwidth': 250,
        'width': 350,
    },
    {
        'text': 'Tipo',
        'iid': 'file_type',
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Tamanho',
        'iid': 'storage_size',
        'anchor': tk.CENTER,
        'minwidth': 80,
        'width': None,
    },
    {
        'text': 'Iniciado',
        'iid': 'date_started',
        'anchor': tk.CENTER,
        'minwidth': 150,
        'width': 180,
    },
    {
        'text': 'Finalizado',
        'iid': 'date_finished',
        'anchor': tk.CENTER,
        'minwidth': 150,
        'width': 180,
    },
)


class _widgets:
    proc_tree: ProcessingTree
    proc_section: ProcessingSection
    proc_button_frame: ProcessingButtonFrame
    proc_btn_start: StartButton
    proc_btn_pause: PauseButton
    proc_btn_stop: StopButton
    proc_btn_add: AddButton
    proc_btn_delete: DeleteButton

    hist_tree: HistoryTree
    hist_section: HistorySection
    hist_button_frame: HistoryButtonFrame
    hist_export_sheet: ExportSheetButton
    hist_export_hist: ExportHistoryButton

    @classmethod
    def register(cls, widget: ttk.Widget | tk.Widget) -> None | Never:
        fields = get_type_hints(cls)
        for name, _type in fields.items():
            if not isinstance(widget, _type):
                continue
            if hasattr(cls, name) and getattr(cls, name, None) is not None:
                raise RuntimeError('widget already assigned to property in class')
            setattr(cls, name, widget)
            return
        raise TypeError(
            'widget is not an instance of any property defined in class type hints'
        )


class Tag:
    RUNNING = 'running'
    """
    Item represents process which is running, but not necessarily performing actions.

    Not having this tag implies the item is not or has never been the subject of any
    running process.
    """
    HALTED = 'halted'
    """
    Item represents process which is running but definitelly not performing actions,
    meaning it is paused/halted in a way that can be resumed later.

    Not having this tag implies the process is running and doing things normally.
    """

    @staticmethod
    def tag_list(tag: str | list[str] | tuple[str, ...]) -> list[str]:
        if tag == '':
            return []
        if isinstance(tag, str):
            return [tag]
        if isinstance(tag, list):
            return tag if len(tag) > 0 else []
        if isinstance(tag, tuple):
            return list(tag) if len(tag) > 0 else []
        raise ValueError('unknown tag argument type')


class ActionButton(ttk.Button):
    def __init__(self, master: ButtonFrame, text: str):
        super().__init__(
            master,
            padding=padding(horizontal=5),
            text=text,
            takefocus=tk.TRUE,
            command=self.on_click,
        )
        self.parent_widget = master
        _widgets.register(self)

    @abstractmethod
    def on_click(self): ...

    def pack(self):
        """Generic .pack() that reverses order of packed widgets so that they appear in
        the the order they were packed.
        """
        super().pack(side=tk.RIGHT, padx=(0, 2))
        # reverse packing order
        buttons = self.parent_widget.buttons
        if len(buttons) > 0:
            self.pack_configure(before=buttons[-1])
        if len(buttons) == 0 or self not in buttons:
            buttons.append(self)

    def disable(self):
        if self['state'] == tk.DISABLED:
            return
        self.config(state=tk.DISABLED)

    def enable(self):
        if self['state'] == tk.NORMAL:
            return
        self.config(state=tk.NORMAL)


class StartButton(ActionButton):
    def on_click(self):
        tree = _widgets.proc_tree
        iid = tree.focus()
        if iid == '' or tree.tag_has(Tag.RUNNING, iid):
            return
        tags = Tag.tag_list(tree.item(iid, 'tags'))
        if len(tags) > 0 and Tag.HALTED in tags:
            tags.remove(Tag.HALTED)
        tags.append(Tag.RUNNING)
        tree.item(iid, tags=tags)


class PauseButton(ActionButton):
    def on_click(self):
        tree = _widgets.proc_tree
        iid = tree.focus()
        if iid == '' or tree.tag_has(Tag.HALTED, iid):
            return
        tags = Tag.tag_list(tree.item(iid, 'tags'))
        if len(tags) > 0 and Tag.RUNNING in tags:
            tags.remove(Tag.RUNNING)
        tags.append(Tag.HALTED)
        tree.item(iid, tags=tags)


class StopButton(ActionButton):
    def on_click(self):
        tree = _widgets.proc_tree
        iid = tree.focus()
        if iid == '':
            return
        tags = Tag.tag_list(tree.item(iid, 'tags'))
        if len(tags) > 0:
            if Tag.RUNNING in tags:
                tags.remove(Tag.RUNNING)
            if Tag.HALTED in tags:
                tags.remove(Tag.HALTED)
        tree.item(iid, tags=tags)


class AddButton(ActionButton):
    def __init__(self, master: ButtonFrame):
        super().__init__(master, 'Adicionar')

    def _insert_to_db(self, value: tuple[Path, ...] | Exception, raised: bool) -> None:
        if raised:
            value = cast(Exception, value)
            raise value
        value = cast(tuple[Path, ...], value)
        for p in value:
            sheetobj = Sheet(p)
            with TkinterGlobal.sqlite.begin() as conn:
                sha = sheetobj.db_workbook.get('sha512', None)
                if sha is None:
                    raise SheetParsing.ValueError('sha512 does not exist')
                query = (
                    select(func.count())
                    .select_from(Workbook)
                    .where(Workbook.sha512 == sha)
                )
                count = conn.execute(query).one_or_none() or 0
                if count > 0:
                    # spreadsheet already exists in db
                    continue
            if len(sheetobj.worksheets) == 0:
                raise SheetParsing.ValueError('no worksheets exist in spreadsheet')
            inserted_id: int = Workbook.sync_insert_one(sheetobj.db_workbook)
            db_sheets = []
            for sheet_dict in sheetobj.db_worksheets:
                _dict = sheet_dict.copy()
                _dict['workbook_id'] = inserted_id
                db_sheets.append(_dict)
            Worksheet.sync_insert_many(*db_sheets)
        _widgets.proc_tree.event_generate('<<ReloadTree>>')

    def on_click(self):
        lock = TkinterLock
        pickable_func = functools.partial(
            open_file_dialog,
            hwnd=self.winfo_id(),
            title='Selecionar Certificado',
            extensions=SHEET_FILEDIALOG_OPTIONS,
            multi_select=True,
        )
        lock.schedule(self, pickable_func, self._insert_to_db, block=False)


class DeleteButton(ActionButton):
    def __init__(self, master: ButtonFrame):
        super().__init__(master, 'Remover')

    def on_click(self):
        iid = _widgets.proc_tree.focus()
        if iid == '':
            return
        _id = int(iid)
        with TkinterGlobal.sqlite.begin() as conn:
            query = select(Worksheet._id).where(Worksheet.workbook_id == _id)
            ids = conn.execute(query).all()
            if len(ids) > 0:
                # no worksheets exist
                del_query = delete(Worksheet).where(Worksheet._id.in_(ids))
                conn.execute(del_query)
            query = select(Workbook._id).where(Workbook._id == _id)
            db_id = conn.execute(query).one_or_none()
            if db_id is not None:
                # workbook doesn't exist
                del_query = delete(Workbook).where(Workbook._id == db_id)
                conn.execute(del_query)
        _widgets.proc_tree.event_generate('<<DeleteSelected>>')


class ExportSheetButton(ActionButton):
    pass


class ExportHistoryButton(ActionButton):
    pass


class UppercaseStringVar(tk.StringVar):
    def __init__(
        self,
        master: tk.Misc | None = None,
        value: str | None = None,
        name: str | None = None,
    ) -> None:
        if value is not None:
            value = value.upper()
        super().__init__(master, value, name)

    def set(self, value: str) -> None:
        return super().set(value.upper())


class ButtonFrame(ttk.Frame):
    def __init__(self, master: ttk.Widget, title: str):
        super().__init__(master)
        _widgets.register(self)
        self.buttons: list[ActionButton] = []
        self.title = UppercaseStringVar(value=title)
        self.create_widgets()

    def pack(self):
        super().pack(anchor=tk.NE, side=tk.TOP, fill=tk.X)
        self.label.pack(side=tk.LEFT, anchor=tk.W, fill=tk.Y)

    def create_widgets(self):
        self.label = ttk.Label(self, textvariable=self.title, padding=padding(left=5))


class ProcessingButtonFrame(ButtonFrame):
    def __init__(self, master: ttk.Widget):
        super().__init__(master, 'Fila de processamento')

    def pack(self):
        super().pack()
        self.start.pack()
        self.pause.pack()
        self.stop.pack()
        self.add.pack()
        self.delete.pack()

    def create_widgets(self):
        super().create_widgets()
        self.start = StartButton(self, 'Começar')
        self.pause = PauseButton(self, 'Pausar')
        self.stop = StopButton(self, 'Parar')
        self.add = AddButton(self)
        self.delete = DeleteButton(self)


class HistoryButtonFrame(ButtonFrame):
    def __init__(self, master: ttk.Widget):
        super().__init__(master, 'Histórico')

    def pack(self):
        super().pack()
        self.export_sheet.pack()
        self.export_history.pack()

    def create_widgets(self):
        super().create_widgets()
        self.export_sheet = ExportSheetButton(self, 'Exportar Planilha')
        self.export_history = ExportHistoryButton(self, 'Exportar Histórico')


class Tree(ttk.Treeview):
    headings_spec: HeadingSequence

    def __init__(self, master: ttk.Widget):
        self.columns = tuple(spec['iid'] for spec in self.headings_spec)

        super().__init__(
            master,
            height=10,
            selectmode=tk.BROWSE,
            takefocus=tk.TRUE,
            columns=self.columns,
            show='headings',
        )

        _widgets.register(self)

        for spec in self.headings_spec:
            iid = spec['iid']
            anchor: Any = spec['anchor']  # string but the typechecker will complain :/
            self.heading(iid, text=spec['text'], anchor=anchor)
            if anchor is not None:
                self.column(iid, anchor=anchor)
            if (minwidth := spec['minwidth']) is not None:
                self.column(iid, minwidth=minwidth)
            if (width := spec['width']) is not None:
                self.column(iid, width=width)

        self.bind('<<TreeviewSelect>>', self._set_button_state)
        self.bind('<Visibility>', self._set_button_state)
        self.bind('<Button-1>', self._check_click_position)

    def _check_click_position(self, event: tk.Event):
        if self.identify_region(event.x, event.y) not in ('heading', 'nothing'):
            return
        self.focus('')
        selection = self.selection()
        if len(selection) == 0:
            return
        self.selection_remove(selection)

    @abstractmethod
    def _set_button_state(self, event: tk.Event): ...

    def pack(self):
        super().pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)

    @abstractmethod
    def _make_row_data(self, data: Any) -> tuple[str, ...]: ...


class ProcessingTree(Tree):
    headings_spec = INPUT_QUEUE

    def __init__(self, master: ttk.Widget):
        super().__init__(master)
        self.bind('<<ReloadTree>>', self.force_reload_tree)
        self.bind('<<DeleteSelected>>', self._delete_selected)

    def _make_file_data(self, db_book: WorkbookDict) -> tuple[str, ...]:
        path = Path(db_book.get('original_path', ''))
        name = unidecode(path.stem)
        name = re_whitespace.sub(' ', name)
        name = name.strip(string.whitespace + string.punctuation)
        description = db_book.get('file_type_description', '')
        file_size = db_book.get('file_size', 0)
        if file_size > 1e6:
            # megabytes ballpark
            sizeof = format(file_size / 1e6, '.2f') + 'MB'
        elif file_size > 1e3:
            # kilobytes ballpark
            sizeof = format(file_size / 1e3, '.2f') + 'KB'
        else:
            # simple bytes ballpark
            sizeof = str(file_size) + 'B'
        if 'created' in db_book:
            datetime_format = '%d/%m/%Y %H:%M'
            created = db_book['created'].strftime(datetime_format)
        else:
            created = ''
        return ('-', name, description, sizeof, created)

    def force_reload_tree(self, event: tk.Event | None = None):
        if Workbook.sync_count() == 0:
            return
        db_books = Workbook.sync_select_all_columns(
            '_id', 'original_path', 'file_type_description', 'file_size', 'created'
        )
        for book in db_books:
            iid = book._id
            values = self._make_file_data(WorkbookDict(**book._asdict()))
            if self.exists(iid):
                self.item(iid, values=values)
                continue
            self.insert('', iid, iid, values=values)

    def _delete_selected(self, event: tk.Event):
        selected = self.selection()
        if len(selected) == 0:
            return
        self.delete(*selected)

    def _set_button_state(self, event):
        iid = self.focus()
        if iid == '':
            _widgets.proc_btn_start.disable()
            _widgets.proc_btn_pause.disable()
            _widgets.proc_btn_stop.disable()
            _widgets.proc_btn_delete.disable()
            return
        if self.tag_has(Tag.RUNNING, iid):
            _widgets.proc_btn_start.disable()
            _widgets.proc_btn_pause.enable()
            _widgets.proc_btn_stop.disable()
            _widgets.proc_btn_delete.disable()
        elif self.tag_has(Tag.HALTED, iid):
            _widgets.proc_btn_start.enable()
            _widgets.proc_btn_pause.disable()
            _widgets.proc_btn_stop.enable()
            _widgets.proc_btn_delete.disable()
        else:
            # isn't part of any process, action, procedure, etc
            _widgets.proc_btn_start.enable()
            _widgets.proc_btn_pause.disable()
            _widgets.proc_btn_stop.disable()
            _widgets.proc_btn_delete.enable()


class HistoryTree(Tree):
    headings_spec = HISTORY

    def _set_button_state(self, event):
        if self.focus() == '':
            _widgets.hist_export_sheet.disable()
        else:
            _widgets.hist_export_sheet.enable()
        if len(self.get_children()) == 0:
            _widgets.hist_export_hist.disable()
        else:
            _widgets.hist_export_hist.enable()


class TreeSection(ttk.Frame):
    def __init__(self, master: ttk.Widget):
        super().__init__(master)
        _widgets.register(self)
        self.create_widgets()

    @abstractmethod
    def create_widgets(self):
        self.button_frame: ButtonFrame
        self.tree: Tree

    def pack(self):
        super().pack(fill=tk.BOTH, expand=tk.TRUE, side=tk.TOP, anchor=tk.NW)
        self.button_frame.pack()
        self.tree.pack()


class ProcessingSection(TreeSection):
    # TODO

    def create_widgets(self):
        self.button_frame = ProcessingButtonFrame(self)
        self.tree = ProcessingTree(self)


class HistorySection(TreeSection):
    # TODO

    def create_widgets(self):
        self.button_frame = HistoryButtonFrame(self)
        self.tree = HistoryTree(self)


class SheetProcess(View):
    def __init__(self, master):
        super().__init__(master)
        self.processing = ProcessingSection(self)
        self.processing.pack()
        self.history = HistorySection(self)
        self.history.pack()
