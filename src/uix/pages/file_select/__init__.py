"""Página de seleção e progresso de processamento de planilhas."""

from kivy.clock import Clock
from typing import Any

from src.uix.pages.base import Page
from src.uix.pages.file_select.progress import ProgressSection
from src.uix.pages.file_select.select_and_add import (
    SelectButtonSection,
    SelectedFileSection,
    AddToQueueSection,
)
from src.utils.io import loadkv

__all__ = ["FileSelectPage"]

loadkv("file_select")


class FileSelectPage(Page):
    """Página de seleção e progresso de processamento de planilhas."""

    def render_frame(self, delta: float) -> None:
        """Calculos feitos a cada frame."""
        for section in self.children:
            section.render_frame()

        for section in (s for s in self.children if isinstance(s, ProgressSection)):
            section.height = self.height - sum(
                s.height for s in self.children if not isinstance(s, ProgressSection)
            )

    def __init__(self, queues: object, **kw: Any):
        super().__init__(**kw)
        self.queues_collection = queues
        self.selected_file_section = SelectedFileSection()
        self.progress_section = ProgressSection()
        self.add_widget(
            SelectButtonSection(
                self.selected_file_section.label, self.progress_section.queue_widget.elements
            )
        )
        self.add_widget(self.selected_file_section)
        self.add_widget(
            AddToQueueSection(
                self.selected_file_section.label,
                self.progress_section.queue_widget.elements,
                queues.arquivos_planilhas,
            )
        )
        self.add_widget(self.progress_section)
        Clock.schedule_interval(self.render_frame, 1 / 60)
