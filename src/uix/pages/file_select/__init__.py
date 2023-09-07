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
    def render_frame(self, delta: float) -> None:
        for section in self.children:
            section.render_frame()

        for section in (s for s in self.children if isinstance(s, ProgressSection)):
            section.height = self.height - sum(
                s.height for s in self.children if not isinstance(s, ProgressSection)
            )

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self.add_widget(SelectButtonSection())
        self.add_widget(SelectedFileSection())
        self.add_widget(AddToQueueSection())
        self.add_widget(ProgressSection())
        Clock.schedule_interval(self.render_frame, 1 / 60)
