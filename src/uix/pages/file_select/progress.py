"""Indicadores de progresso no processamento das planilhas."""

import time
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from typing import Any
from multiprocessing import RLock

from src.uix.pages.file_select.queue import QueueLayout
from src.uix.pages.file_select.bases import FileSelectSection
from src.uix.style_guides import Sizes
from src.async_vitals.messaging import ProgressStateNamespace as progress_values_t

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

    def on_value(self, widget: Widget, value: int) -> None:
        if self.count_label.max == 0 or value == 0:
            # Número absurdamente pequeno pq 0 não funciona
            self.bar_filling.size = (1e-12, self.bar_filling.size[1])
            return None
        self.bar_filling.size = (
            value * (self.width / self.count_label.max),
            self.bar_filling.size[1],
        )

    def __init__(self, count_label: Label, **kw: Any) -> None:
        super().__init__(**kw)
        self.count_label = count_label
        self.bar_filling = self.canvas.get_group("progress_indicator")[0]


class ProgressStatusBar(RelativeLayout):
    """Container de uma barra de progresso contendo a própria barra, texto indicando o progresso,
    texto indicando o item sendo processado no momento e um texto dando uma descrição do item sendo
    processado."""

    def update(
        self, position: int, value: str = "", description: str | None = None, lock: bool = True
    ) -> None:
        """Atualizar de forma geral as informações que indicam o progresso (aparência da barra e
        textos indicativos)."""
        if lock:
            self.lock.acquire()

        if description is None:
            description = "Aguardando planilha..."

        self.bar.value = position
        self.value_label.text = "[b]" + self.prefix + "[/b]" + value
        self.description_label.text = description
        self.count_label.value = position

        if lock:
            self.lock.release()

    def reset(self, max_count: int = 0, lock: bool = True) -> None:
        """Resetar progresso."""
        if lock:
            self.lock.acquire()

        self.count_label.max = max_count
        self.update(0, lock=False)

        if lock:
            self.lock.release()

    def __init__(self, prefix: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.lock = RLock()
        self.prefix = prefix
        self.value_label = ProgressLabel()
        self.description_label = ProgressDescription()
        self.count_label = ProgressCount()
        self.bar = ProgressBarIndicator(self.count_label)

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

    def update_progress(self) -> None:
        """Atualizar progresso do processamento com base nas propriedades compartilhadas entre os
        processos."""
        if self._was_previously_set and not self.started_event.is_set():
            self.progress_widget.cnpj_progress.reset()
            self.progress_widget.cpf_progress.reset()

            # MOVING TEXTS
            for i in range(len(self.queue_widget.elements)):
                next_one = next(el for el in self.queue_widget.elements if el.order == i + 1)
                if next_one.order == 1:
                    next_one.update()
                    continue
                elif next_one.full_path is None:
                    continue
                previous_one = next(el for el in self.queue_widget.elements if el.order == i)
                previous_one.update(next_one.full_path)
                next_one.update()

            self._was_previously_set = False
            return None
        elif not self.started_event.is_set():
            return None
        elif (not self._was_previously_set) and self.started_event.is_set():
            with self.progress_values.get_lock():
                self.progress_widget.cnpj_progress.reset(self.progress_values.cnpj_max)
                self.progress_widget.cpf_progress.reset(self.progress_values.cpf_max)
                self.progress_widget.cnpj_progress.update(
                    self.progress_values.cnpj_current,
                    progress_values_t.get_string(self.progress_values.cnpj_msg),
                    progress_values_t.get_string(self.progress_values.cnpj_long_msg),
                )
                self.progress_widget.cpf_progress.update(
                    self.progress_values.cpf_current,
                    progress_values_t.get_string(self.progress_values.cpf_msg),
                    progress_values_t.get_string(self.progress_values.cpf_long_msg),
                )
            t = time.time_ns()
            self._last_updated_cnpj = t
            self._last_updated_cpf = t
            self._last_updated_cnpj_max = t
            self._last_updated_cpf_max = t
            self._was_previously_set = True
            return None

        with self.progress_widget.cnpj_progress.lock, self.progress_values.get_lock():
            if (
                self.progress_widget.cnpj_progress.count_label.max != self.progress_values.cnpj_max
                and self.progress_values.cnpj_max_last_updated_ns > self._last_updated_cnpj_max
            ):
                if self.progress_values.cnpj_max < 0:
                    raise ValueError("Número máximo de itens não pode ser negativo.")
                self.progress_widget.cnpj_progress.reset(self.progress_values.cnpj_max, lock=False)
                self._last_updated_cnpj_max = time.time_ns()

        with self.progress_widget.cpf_progress.lock, self.progress_values.get_lock():
            if (
                self.progress_widget.cpf_progress.count_label.max != self.progress_values.cpf_max
                and self.progress_values.cpf_max_last_updated_ns > self._last_updated_cpf_max
            ):
                if self.progress_values.cpf_max < 0:
                    raise ValueError("Número máximo de itens não pode ser negativo.")
                self.progress_widget.cpf_progress.reset(self.progress_values.cpf_max, lock=False)
                self._last_updated_cpf_max = time.time_ns()

        with self.progress_values.get_lock():
            if self.progress_values.cnpj_last_updated_ns > self._last_updated_cnpj:
                self.progress_widget.cnpj_progress.update(
                    self.progress_values.cnpj_current,
                    progress_values_t.get_string(self.progress_values.cnpj_msg),
                    progress_values_t.get_string(self.progress_values.cnpj_long_msg),
                )
                self._last_updated_cnpj = time.time_ns()
            if self.progress_values.cpf_last_updated_ns > self._last_updated_cpf:
                self.progress_widget.cpf_progress.update(
                    self.progress_values.cpf_current,
                    progress_values_t.get_string(self.progress_values.cpf_msg),
                    progress_values_t.get_string(self.progress_values.cpf_long_msg),
                )
                self._last_updated_cpf = time.time_ns()

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

        self.update_progress()

    def __init__(
        self,
        started_event: object,
        progress_values: progress_values_t,
        **kw: Any,
    ) -> None:
        self._was_previously_set: bool = False
        self._last_updated_cnpj: int = 0
        self._last_updated_cpf: int = 0
        self._last_updated_cnpj_max: int = 0
        self._last_updated_cpf_max: int = 0
        super().__init__(**kw)
        self.started_event = started_event
        self.progress_values = progress_values
        self.queue_widget = QueueLayout()
        self.progress_widget = ProgressLayout()
        self.add_widget(self.queue_widget)
        self.add_widget(self.progress_widget)
