"""Elementos que permitem a seleção de planilhas e adição das mesmas à fila de processamento."""

from kivy.uix.label import Label
from kivy.uix.button import Button
from typing import Any

from src.uix.pages.file_select.bases import FileSelectSection
from src.uix.style_guides import Sizes

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

    text = "Selecione um arquivo..."


class SelectButton(Button):
    """Botão que permite a seleção de arquivos."""


class AddToQueueButton(Button):
    """Botão que permite a adição de planilhas para o processamento."""


class SelectButtonSection(FileSelectSection):
    """Seção/container para o botão de seleção de arquivo."""

    def render_frame(self) -> None:
        """Calculos feitos a cada frame."""
        super().render_frame()
        self.height = self.button.height + Sizes.Page.FileSelect.margin_between * 2
        self.button.center = (self.width / 2, self.height / 2)

    def __init__(self, **kw: Any) -> None:
        self.button = SelectButton()
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

    def __init__(self, **kw: Any) -> None:
        self.button = AddToQueueButton()
        super().__init__(**kw)
        self.add_widget(self.button)
