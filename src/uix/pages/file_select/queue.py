from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from typing import Any

from src.uix.style_guides import Sizes, Colors

__all__ = ["QueueElement", "QueueElementNumber", "QueueLayout", "QueueTitle"]


class QueueElementNumber(Label):
    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]


class QueueElement(Label):
    def __init__(self, order: int, **kw: Any) -> None:
        self.order = order
        self.number_widget = QueueElementNumber(text="{}.".format(self.order))
        super().__init__(**kw)
        self.add_widget(self.number_widget)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]

        if order % 2 == 0:
            self.background_color_obj.rgba = Colors.white
            self.number_widget.background_color_obj.rgba = Colors.white


class QueueTitle(Label):
    pass


class QueueLayout(RelativeLayout):
    def render_frame(self) -> None:
        elements = [e for e in self.children if isinstance(e, QueueElement)]
        for i, elem in enumerate(elements):
            elem.y = elem.number_widget.y = elem.height * i

        self.title_widget.x = Sizes.Page.FileSelect.text_padding_small
        self.title_widget.y = (
            sum(elem.height for elem in elements) + Sizes.Page.FileSelect.text_padding_small
        )

        self.width = Sizes.Page.FileSelect.queue_element_total_width
        self.height = self.title_widget.top

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.title_widget = QueueTitle()
        self.add_widget(self.title_widget)
        for i in range(Sizes.Page.FileSelect.amount_queue_elements):
            self.add_widget(QueueElement(i + 1))
