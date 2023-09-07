"""Indicadores de progresso no processamento das planilhas."""

from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.progressbar import ProgressBar
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
    """Contador do progresso da barra, como em ``3 de 8``."""

    _max = 0
    _value = 0

    @property
    def max(self) -> int:
        """Número máximo do contador e indicador do número total de itens que devem ser
        processados."""
        return self._max

    @max.setter
    def max(self, value: int) -> None:
        if value < 0:
            raise ValueError("Valor máximo não pode ser menor que zero.")
        self._max = value
        self.value = 0

    @property
    def value(self) -> int:
        """Número de itens processados atualmente."""
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
    """Valor do item atual sendo processado, como o CPF ou CNPJ, por exemplo."""


class ProgressDescription(Label):
    """Elemento da descrição do item atual sendo processado, como nome da empresa ou qualquer outra
    informação descritiva."""


class ProgressBarIndicator(ProgressBar):
    """Elemento da barra de progresso."""


class ProgressStatusBar(RelativeLayout):
    """Container de uma barra de progresso contendo a própria barra, texto indicando o progresso,
    texto indicando o item sendo processado no momento e um texto dando uma descrição do item sendo
    processado."""

    def update(self, position: int, value: str = "", description: str | None = None) -> None:
        """Atualizar de forma geral as informações que indicam o progresso (aparência da barra e
        textos indicativos)."""
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
    """Container com a parte que indica o progresso detalhado do processamento."""

    def render_frame(self) -> None:
        """Calculos feitos a cada frame."""
        self.height = self.cnpj_progress.height + self.cpf_progress.height
        self.cnpj_progress.y = self.cpf_progress.height

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.cnpj_progress = ProgressStatusBar("CNPJ: ")
        self.cpf_progress = ProgressStatusBar("CPF: ")
        self.add_widget(self.cnpj_progress)
        self.add_widget(self.cpf_progress)


class ProgressSection(FileSelectSection):
    """Seção que indica o progresso geral do processamento, como a fila de processamento e os
    detalhes do progresso."""

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
