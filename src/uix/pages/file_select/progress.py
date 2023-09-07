from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.progressbar import ProgressBar
from kivy.properties import NumericProperty  # type: ignore
from typing import Any

from src.uix.pages.file_select.queue import QueueLayout
from src.uix.pages.file_select.bases import FileSelectSection
from src.uix.style_guides import Sizes

__all__ = [
    "ProgressBarIndicator",
    "ProgressCount",
    "ProgressDescription",
    "ProgressLabel",
    "ProgressLayout",
    "ProgressSection",
    "ProgressStatusBar",
]


class ProgressCount(Label):
    _max = 0
    _value = 0

    @property
    def max(self) -> int:
        return self._max

    @max.setter
    def max(self, value: int) -> None:
        if value < 0:
            raise ValueError("Valor máximo não pode ser menor que zero.")
        self._max = value
        self.value = 0

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        if value > self.max or value < 0:
            raise ValueError(
                "Valor não pode ser maior ou menor que {} ou menor que zero.".format(self.max)
            )
        self._value = value
        self.text = "{} de {}".format(value, self.max)


class ProgressLabel(Label):
    pass


class ProgressDescription(Label):
    pass


class ProgressBarIndicator(ProgressBar):
    pass


class ProgressStatusBar(RelativeLayout):
    def update(self, position: int, value: str = "", description: str | None = None) -> None:
        if description is None:
            description = "Aguardando planilha..."

        self.bar.value = position
        self.value_label.text = "[b]" + self.prefix + "[/b]" + value
        self.description_label.text = description
        self.count_label.value = position

    def __init__(self, prefix: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.prefix = prefix
        self.value_label = ProgressLabel()
        self.description_label = ProgressDescription()
        self.count_label = ProgressCount()
        self.bar = ProgressBarIndicator()

        self.add_widget(self.value_label)
        self.add_widget(self.description_label)
        self.add_widget(self.count_label)
        self.add_widget(self.bar)

        self.update(0)


class ProgressLayout(RelativeLayout):
    def render_frame(self) -> None:
        self.height = self.cnpj_progress.height + self.cpf_progress.height
        self.cnpj_progress.y = self.cpf_progress.height

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.cnpj_progress = ProgressStatusBar("CNPJ: ")
        self.cpf_progress = ProgressStatusBar("CPF: ")
        self.add_widget(self.cnpj_progress)
        self.add_widget(self.cpf_progress)


class ProgressSection(FileSelectSection):
    def render_frame(self) -> None:
        super().render_frame()
        self.progress_widget.center_y = self.queue_widget.center_y = self.center_y
        self.progress_widget.x = self.queue_widget.width + Sizes.Page.FileSelect.margin_between

        content_width = self.progress_widget.right
        center_difference = (self.width - content_width) / 2
        self.progress_widget.x += center_difference
        self.queue_widget.x = center_difference

        self.queue_widget.render_frame()
        self.progress_widget.render_frame()

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.queue_widget = QueueLayout()
        self.progress_widget = ProgressLayout()
        self.add_widget(self.queue_widget)
        self.add_widget(self.progress_widget)
