"""Elementos que permitem a seleção de planilhas e adição das mesmas à fila de processamento."""

from aioprocessing.queues import AioQueue
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from typing import Any, List
from tkinter.filedialog import askopenfilename
from os.path import basename

from src.uix.pages.file_select.bases import FileSelectSection
from src.uix.style_guides import Colors, Sizes

__all__ = [
    "AddToQueueButton",
    "AddToQueueSection",
    "SelectButton",
    "SelectButtonSection",
    "SelectedFileLabel",
    "SelectedFileSection",
]


class SelectedFileLabel(Label):
    """Texto indicativo do arquivo selecionado."""

    def update(self, path: str | None = None) -> None:
        if not path:
            self.full_path = None
            self.text = "Selecione um arquivo..."
            return None
        self.full_path = path
        self.text = basename(self.full_path)

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.full_path: str | None = None
        self.update()


class SelectButton(Button):
    """Botão que permite a seleção de arquivos."""

    def on_press(self) -> None:
        self.background_color_obj.rgba = Colors.dark_red

    def on_release(self) -> None:
        self.background_color_obj.rgba = Colors.light_red
        filename = askopenfilename(
            filetypes=(("Excel 2007 ou superior", ".xlsx"), ("Excel pré-2007", ".xls"))
        )
        if filename and filename in [elem.full_path for elem in self.elements]:
            return None
        if filename and filename != self.label.full_path:
            self.label.update(filename)

    def __init__(self, label: Label, queue_elements: List[Widget], **kw: Any) -> None:
        super().__init__(**kw)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]
        self.label = label
        self.elements = queue_elements


class AddToQueueButton(Button):
    """Botão que permite a adição de planilhas para o processamento."""

    def on_press(self) -> None:
        self.background_color_obj.rgba = Colors.dark_blue

    def on_release(self) -> None:
        self.background_color_obj.rgba = Colors.light_blue
        if not self.label.full_path:
            return None
        lowest_not_populated = min(elem.order for elem in self.elements if not elem.text)
        next(e for e in self.elements if e.order == lowest_not_populated).update(
            self.label.full_path
        )
        self.label.update()
        self.schedulling_queue.put(self.label.full_path)

    def __init__(
        self, label: Label, queue_elements: List[Widget], schedulling_queue: AioQueue, **kw: Any
    ) -> None:
        super().__init__(**kw)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]
        self.label = label
        self.elements = queue_elements
        self.schedulling_queue = schedulling_queue


class SelectButtonSection(FileSelectSection):
    """Seção/container para o botão de seleção de arquivo."""

    def render_frame(self) -> None:
        """Calculos feitos a cada frame."""
        super().render_frame()
        self.height = self.button.height + Sizes.Page.FileSelect.margin_between * 2
        self.button.center = (self.width / 2, self.height / 2)

    def __init__(self, label: Label, queue_elements: List[Widget], **kw: Any) -> None:
        self.button = SelectButton(label, queue_elements)
        super().__init__(**kw)
        self.add_widget(self.button)


class SelectedFileSection(FileSelectSection):
    """Seção/container para o texto indicativo do arquivo selecionado."""

    def render_frame(self) -> None:
        """Calculos feitos a cada frame."""
        super().render_frame()
        self.height = self.label.height + Sizes.Page.FileSelect.margin_between * 2
        self.label.center = (self.width / 2, self.height / 2)

    def __init__(self, **kw: Any) -> None:
        self.label = SelectedFileLabel()
        super().__init__(**kw)
        self.add_widget(self.label)


class AddToQueueSection(FileSelectSection):
    """Seção/container para o botão de adição da planilha à fila."""

    def render_frame(self) -> None:
        """Calculos feitos a cada frame."""
        super().render_frame()
        self.height = self.button.height + Sizes.Page.FileSelect.margin_between * 2
        self.button.center = (self.width / 2, self.height / 2)

    def __init__(
        self, label: Label, queue_elements: List[Widget], schedulling_queue: AioQueue, **kw: Any
    ) -> None:
        self.button = AddToQueueButton(label, queue_elements, schedulling_queue)
        super().__init__(**kw)
        self.add_widget(self.button)
