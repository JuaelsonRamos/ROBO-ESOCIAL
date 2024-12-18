from __future__ import annotations

from src.gui.utils.units import padding
from src.gui.views.View import View

import tkinter as tk
import tkinter.ttk as ttk

from abc import abstractmethod
from typing import Any, Callable, Never, TypedDict, get_type_hints


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
    pass


class ActionButton(ttk.Button):
    def __init__(self, master: ButtonFrame, text: str):
        super().__init__(
            master, padding=padding(horizontal=5), text=text, takefocus=tk.TRUE
        )
        self.parent_widget = master
        _widgets.register(self)

    def set_command(self, command: Callable):
        """Formal way of setting the buttons' command."""
        self.config(command=command)

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
    pass


class PauseButton(ActionButton):
    pass


class StopButton(ActionButton):
    pass


class AddButton(ActionButton):
    pass


class DeleteButton(ActionButton):
    pass


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
        self.add = AddButton(self, 'Adicionar')
        self.delete = DeleteButton(self, 'Remover')


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

    def pack(self):
        super().pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)

    @abstractmethod
    def _make_row_data(self, data: Any) -> tuple[str, ...]: ...


class ProcessingTree(Tree):
    headings_spec = INPUT_QUEUE
    # TODO


class HistoryTree(Tree):
    headings_spec = HISTORY
    # TODO


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
