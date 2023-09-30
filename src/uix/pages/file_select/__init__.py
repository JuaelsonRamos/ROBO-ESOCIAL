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
            # TODO Rodar render_frame da seção de progresso menos vezes (1 / 30?)

        for section in (s for s in self.children if isinstance(s, ProgressSection)):
            section.height = self.height - sum(
                s.height for s in self.children if not isinstance(s, ProgressSection)
            )

    def __init__(
        self,
        to_process_queue: object,
        started_event: object,
        progress_values: object,
        **kw: Any,
    ):
        super().__init__(**kw)
        self.to_process_queue = to_process_queue
        self.selected_file_section = SelectedFileSection()
        self.progress_section = ProgressSection(started_event, progress_values)
        self.add_widget(
            SelectButtonSection(
                self.selected_file_section.label,
                self.progress_section.queue_widget.elements,
                to_process_queue,
            )
        )
        self.add_widget(self.selected_file_section)
        self.add_widget(
            AddToQueueSection(
                self.selected_file_section.label,
                self.progress_section.queue_widget.elements,
                to_process_queue,
                self.progress_section.queue_widget.element_count,
                self.progress_section.queue_widget.lock,
            )
        )
        self.add_widget(self.progress_section)
        Clock.schedule_interval(self.render_frame, 1 / 60)
