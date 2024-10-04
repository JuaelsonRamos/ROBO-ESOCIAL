"""Fila de processamento de planilhas."""

from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from typing import Any
from os.path import basename
from threading import Lock

from src.uix.style_guides import Sizes, Colors

__all__ = [
    "QueueElement",
    "QueueElementNumber",
    "QueueElementsCount",
    "QueueLayout",
    "QueueScroll",
    "QueueScrollLayout",
    "QueueTitle",
]


class QueueElementNumber(Label):
    """Número indicador da posição da planilha na fila."""

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]


class QueueElement(Label):
    """Elemento da que indica uma planilha na fila."""

    def update(self, path: str | None = None) -> None:
        if not path:
            self.full_path = None
            self.text = ""
            return None
        self.full_path = path
        self.text = basename(path)

    def __init__(self, order: int, **kw: Any) -> None:
        self.order = order
        self.full_path: str | None = None
        self.number_widget = QueueElementNumber(text="{}.".format(self.order))
        super().__init__(**kw)
        self.add_widget(self.number_widget)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]

        if order % 2 == 0:
            self.background_color_obj.rgba = Colors.white
            self.number_widget.background_color_obj.rgba = Colors.white


class QueueTitle(Label):
    """Título da fila de processamento."""


class QueueScrollLayout(RelativeLayout):
    pass


class QueueElementsCount(Label):
    prefix = "Itens na fila: "

    def update(self, amount: int) -> None:
        self.text = "[b]{}[/b]{}".format(self.prefix, amount)

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.update(0)


class QueueScroll(ScrollView):
    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.layout = QueueScrollLayout()
        self.add_widget(self.layout)


class QueueLayout(RelativeLayout):
    """Container contendo todos os widgets da fila."""

    def render_frame(self) -> None:
        """Calculos feitos a cada frame."""
        for elem in self.elements:
            elem.y = elem.number_widget.y = elem.height * (len(self.elements) - elem.order)

        self.title_widget.x = Sizes.Page.FileSelect.text_padding_small
        self.title_widget.y = self.scroll.top + Sizes.Page.FileSelect.text_padding_small

        self.width = Sizes.Page.FileSelect.queue_element_total_width
        self.height = self.title_widget.top

        self.scroll.y = self.element_count.top + Sizes.Page.FileSelect.text_padding_small
        self.scroll.layout.height = sum(el.height for el in self.scroll.layout.children)

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.title_widget = QueueTitle()
        self.elements = []
        self.scroll = QueueScroll()
        self.element_count = QueueElementsCount()
        self.lock = Lock()
        self.add_widget(self.title_widget)
        self.add_widget(self.scroll)
        self.add_widget(self.element_count)
        for i in range(Sizes.Page.FileSelect.amount_queue_elements):
            self.elements.append(QueueElement(i + 1))
            self.scroll.layout.add_widget(self.elements[i])
