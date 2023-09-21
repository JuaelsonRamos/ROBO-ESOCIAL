from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView

from typing import Any, List, Tuple
from src.uix.style_guides import Colors, Sizes

from src.utils.io import geticon, loadkv


__all__ = ["PopUpButton", "PopUpIcon", "PopUpLabel", "PopUpLayout", "PopUpMessage"]

loadkv("popup_message")


class PopUpIcon(Image):
    """Icone da janela de Pop Up."""


class PopUpLabel(Label):
    """Mensagem da janela de Pop Up."""


class PopUpButton(Button):
    """Botão de opção dentro da janela de Pop Up."""

    def on_press(self) -> None:
        self.background_color_obj.rgba = Colors.gray

    def on_release(self) -> None:
        self.background_color_obj.rgba = Colors.white

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]


class PopUpLayout(RelativeLayout):
    """Conteúdo da janela de Pop Up."""

    message_widget = PopUpLabel(text="DEBUG!")
    icon_widget = PopUpIcon(source=geticon("icone_desconhecido"))

    def set_message_and_icon(
        self, icon: str = geticon("icone_desconhecido"), message: str = ""
    ) -> None:
        self.icon_widget.source = icon
        self.message_widget.text = message

    def position_widgets(self) -> None:
        for button in self.buttons:
            button.y = Sizes.PopUpMessage.margin
            if len(self.buttons) == 1:
                button.center_x = self.center_x

        self.icon_widget.center_x = self.center_x
        self.icon_widget.y = (
            Sizes.PopUpMessage.window_height
            - Sizes.PopUpMessage.margin / 2
            - self.icon_widget.height
        )

        self.message_widget.center_x = self.center_x
        self.message_widget.center_y = (
            self.icon_widget.y - self.buttons[0].top
        ) / 2 + self.buttons[0].top

    def resize_widgets(self) -> None:
        # ICON
        if self.icon_widget.texture_size[0] > self.icon_widget.texture_size[1]:
            # max width  80 -> 10 texture width
            # max height  x -> 12 texture height
            rule_of_three = self.icon_widget.texture_size[0] / (
                Sizes.PopUpMessage.max_icon_size * self.icon_widget.texture_size[1]
            )
            self.icon_widget.width = Sizes.PopUpMessage.max_icon_size
            self.icon_widget.height = rule_of_three
        elif self.icon_widget.texture_size[0] == self.icon_widget.texture_size[1]:
            self.icon_widget.width = self.icon_widget.height = Sizes.PopUpMessage.max_icon_size
        else:
            rule_of_three = self.icon_widget.texture_size[1] / (
                Sizes.PopUpMessage.max_icon_size * self.icon_widget.texture_size[0]
            )
            self.icon_widget.width = rule_of_three
            self.icon_widget.height = Sizes.PopUpMessage.max_icon_size

        self.icon_widget.texture_size = self.icon_widget.size

    def __init__(self, buttons: List[PopUpButton], **kw: Any) -> None:
        self.buttons = buttons
        super().__init__(**kw)
        self.add_widget(self.message_widget)
        self.add_widget(self.icon_widget)
        for b in self.buttons:
            self.add_widget(b)


class PopUpMessage(ModalView):
    """Classe base para qualquer mensagem de Pop Up."""

    def _open(self, icon_path: str, message: str, color: Tuple[float, ...] = Colors.black) -> None:
        self.layout_widget.set_message_and_icon(icon_path, message)
        self.layout_widget.position_widgets()
        self.layout_widget.icon_widget.color = color
        self.open()

    def info(self, message: str) -> None:
        self._open(geticon("info"), message, Colors.dark_blue)

    def error(self, message: str) -> None:
        self._open(geticon("erro"), message, Colors.dark_red)

    def __init__(self, buttons: List[PopUpButton], **kw: Any) -> None:
        self.layout_widget = PopUpLayout(buttons)
        super().__init__(**kw)
        self.add_widget(self.layout_widget)


def _ask_ok_factory() -> PopUpMessage:
    ok_btn = PopUpButton(text="Ok!")
    popup = PopUpMessage([ok_btn])
    ok_btn.bind(on_release=popup.dismiss)
    return popup


ask_ok = _ask_ok_factory()
