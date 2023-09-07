"""Página de seleção de páginas."""

from kivy.uix.button import Button
from kivy.clock import Clock
from typing import Any

from src.uix.pages.base import Page
from src.utils.io import loadkv
from src.uix.pages.home.sections import ManagementSection, CoralSection, StatisticsSection

__all__ = ["HomePage"]

loadkv("home")


class HomePage(Page):
    """Página de seleção de páginas."""

    identifier = "home"

    def render_frame(self, delta: float) -> None:
        """Calculos feitos a cada frame."""
        for section in self.children:
            section.height = self.height / len(self.children)
            section.render_frame()

    def __init__(
        self,
        events_button: Button,
        file_select_button: Button,
        statistics_button: Button,
        certificates_button: Button,
        info_button: Button,
        **kw: Any,
    ) -> None:
        super().__init__(**kw)
        self.add_widget(ManagementSection(file_select_button, certificates_button))
        self.add_widget(StatisticsSection(events_button, statistics_button))
        self.add_widget(CoralSection(info_button))

        Clock.schedule_interval(self.render_frame, 1 / 60)
