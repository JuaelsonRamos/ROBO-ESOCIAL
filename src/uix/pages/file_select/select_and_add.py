"""Elementos que permitem a seleção de planilhas e adição das mesmas à fila de processamento."""

from threading import Lock
from aioprocessing.queues import AioQueue
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from typing import Any, List
from tkinter.filedialog import askopenfilenames
from os.path import basename

from src.uix.pages.file_select.bases import FileSelectSection
from src.uix.pages.file_select.queue import QueueElement
from src.uix.style_guides import Colors, Sizes
from src.uix.popup.message import ask_ok

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

    def update(self, path_list: List[str] | None = None) -> None:
        if not path_list:
            self.full_path = None
            self.text = "Selecione um arquivo..."
            return None

        if len(path_list) == 0:
            return None

        self.full_path = path_list
        if len(self.full_path) == 1:
            self.text = basename(self.full_path[0])
            return None
        self.text = "{} arquivos selecionados.".format(len(self.full_path))

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.full_path: List[str] | None = None
        self.update()


class SelectButton(Button):
    """Botão que permite a seleção de arquivos."""

    def on_press(self) -> None:
        self.background_color_obj.rgba = Colors.dark_red

    def on_release(self) -> None:
        self.background_color_obj.rgba = Colors.light_red
        if self.to_process_queue.full():
            ask_ok.error("A fila de processamento está cheia!")
            return None
        filename = askopenfilenames(
            filetypes=(("Excel 2007 ou superior", ".xlsx"), ("Excel pré-2007", ".xls"))
        )

        if (not filename) or len(filename) == 0:
            return None

        file_count: int = 0
        unique: List[str] = []
        for file in filename:
            if file in (elem.full_path for elem in self.elements):
                file_count += 1
                continue
            unique.append(file)

        if file_count == len(filename):
            lock = ask_ok.error("Todos os arquivos selecionados já estão na fila de processamento.")
            if lock:
                with lock:
                    return None
        elif file_count > 0:
            lock = ask_ok.info(
                "Encontrados {} arquivos que já estão presentes na fila de processamento. Pulando estes desta vez.".format(
                    file_count
                )
            )
            if lock:
                with lock:
                    pass

        self.label.update(unique)

    def __init__(
        self, label: Label, queue_elements: List[Widget], to_process_queue: AioQueue, **kw: Any
    ) -> None:
        super().__init__(**kw)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]
        self.label = label
        self.to_process_queue = to_process_queue
        self.elements = queue_elements


class AddToQueueButton(Button):
    """Botão que permite a adição de planilhas para o processamento."""

    def on_press(self) -> None:
        self.background_color_obj.rgba = Colors.dark_blue

    def on_release(self) -> None:
        self.background_color_obj.rgba = Colors.light_blue
        self.queue_elements_lock.acquire()
        if not self.label.full_path:
            return None
        howmany_empty = sum(1 for elem in self.elements if elem.full_path is None)
        highest_populated = max(
            (elem.order for elem in self.elements if elem.full_path is not None), default=0
        )
        if len(self.elements) > Sizes.Page.FileSelect.amount_queue_elements or howmany_empty == 0:
            # A quantidade de elementos na fila já excedeu o limite mínimo e há uma garantia de que
            # para comportar mais, novos elementos devem ser criados.
            for i, filename in enumerate(self.label.full_path):
                self.elements.append(QueueElement(highest_populated + 1 + i))
                self.elements[-1].update(filename)
                self.to_process_queue.put(filename)
            self.label.update()
        elif len(self.label.full_path) <= howmany_empty:
            # A quantidade de elementos na fila é igual ao limite mínimo.
            # Há uma garantia de que não é preciso criar novos elementos para comportar todos
            # os arquivos selecionados.
            lowest_not_populated = min(
                elem.order for elem in self.elements if elem.full_path is None
            )
            for el, file in zip(
                (elem for elem in self.elements if elem.order >= lowest_not_populated),
                self.label.full_path,
            ):
                el.update(file)
                self.to_process_queue.put(file)
            self.label.update()
        else:
            # Aqui eu tenho uma quantidade de elementos vazios dentro do limite mínimo.
            # A quantidade de arquivos selecionados é suficiente para preencher todos estes, assim
            # como uma quantidade positiva de novos.
            delta: int = len(self.elements) - highest_populated
            lowest_empty = min(el.order for el in self.elements if el.full_path is None)
            for i, file in enumerate(self.label.full_path[:delta]):
                next(el for el in self.elements if el.order == lowest_empty + i).update(file)
                self.to_process_queue.put(file)

            for i, file in enumerate(self.label.full_path[delta:]):
                self.elements.append(
                    QueueElement(Sizes.Page.FileSelect.amount_queue_elements + i + 1)
                )
                self.elements[-1].update(file)
                self.to_process_queue.put(file)

            self.label.update()

        self.element_count.update(sum(1 for el in self.elements if el.full_path is not None))
        self.queue_elements_lock.release()

    def __init__(
        self,
        label: Label,
        queue_elements: List[Widget],
        to_process_queue: AioQueue,
        element_count: Label,
        queue_elements_lock: Lock,
        **kw: Any,
    ) -> None:
        super().__init__(**kw)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]
        self.label = label
        self.elements = queue_elements
        self.to_process_queue = to_process_queue
        self.element_count = element_count
        self.queue_elements_lock = queue_elements_lock


class SelectButtonSection(FileSelectSection):
    """Seção/container para o botão de seleção de arquivo."""

    def render_frame(self) -> None:
        """Calculos feitos a cada frame."""
        super().render_frame()
        self.height = self.button.height + Sizes.Page.FileSelect.margin_between * 2
        self.button.center = (self.width / 2, self.height / 2)

    def __init__(
        self, label: Label, queue_elements: List[Widget], to_process_queue: AioQueue, **kw: Any
    ) -> None:
        self.button = SelectButton(label, queue_elements, to_process_queue)
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
        self,
        label: Label,
        queue_elements: List[Widget],
        to_process_queue: AioQueue,
        element_count: Label,
        queue_elements_lock: Lock,
        **kw: Any,
    ) -> None:
        self.button = AddToQueueButton(
            label, queue_elements, to_process_queue, element_count, queue_elements_lock
        )
        super().__init__(**kw)
        self.add_widget(self.button)
