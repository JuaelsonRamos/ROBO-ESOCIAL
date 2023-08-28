"""Barra de navegação."""

from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window  # type: ignore
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from typing import Any, Dict

from src.local.types import Int
from src.utils.io import loadkv

__all__ = [
    "CertificatesButton",
    "EventsButton",
    "FileSelectButton",
    "HomeButton",
    "InfoButton",
    "Nav",
    "NavButton",
    "StatisticsButton",
]

loadkv("nav")


class NavButton(ToggleButton):
    """Botão da barra de navegação de páginas."""

    order_position_top = Int(0)
    order_position_bottom = Int(0)
    margin_between = Int(10)

    kv_opts: Dict[str, Any] = dict(size=(60, 60), size_hint=(None, None))

    def _calc_y_nocheck(self) -> None:
        order = self.order_position_bottom or self.order_position_top
        if self.order_position_top:
            self.y = Window.height - (self.margin_between * order + self.height * order)
        else:
            self.y = self.margin_between * order + (self.height * (order - 1))

    def _calc_y(self) -> None:
        if self.order_position_bottom > 0 and self.order_position_top > 0:
            raise ValueError(
                "A button can only be either on top or on bottom. A position order was specified for both top and bottom."
            )
        elif self.order_position_bottom < 0 or self.order_position_top < 0:
            raise ValueError("A position order can't be negative.")

        self._calc_y_nocheck()

    def render_frame(self, delta: float) -> None:
        """Realizar cálculos que precisam ser feitos a cada frame.

        :param delta: Variação de tempo.
        """
        self._calc_y_nocheck()

    def __init__(self, **kw: Any):
        self.kv_opts.update(kw)
        super().__init__(**self.kv_opts)
        self._calc_y()

        Clock.schedule_interval(self.render_frame, 1 / 60)


class HomeButton(NavButton):
    """Botão para a página de seleção de páginas."""

    order_position_top = 1


class FileSelectButton(NavButton):
    """Botão para a página de seleção de planilhas."""

    order_position_top = 2


class CertificatesButton(NavButton):
    """Botão para a página de gerenciamento de certificados."""

    order_position_top = 3


class EventsButton(NavButton):
    """Botão para a página de log de eventos do processamento da planilha."""

    order_position_top = 4


class StatisticsButton(NavButton):
    """Botão para a página de visualização de estatísticas sobre processamento das planilhas."""

    order_position_top = 5


class InfoButton(NavButton):
    """Botão para a página de informações e configurações."""

    order_position_bottom = 1


class Nav(FloatLayout):
    """Barra de navegação."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.add_widget(HomeButton())
        self.add_widget(InfoButton())
        self.add_widget(EventsButton())
        self.add_widget(FileSelectButton())
        self.add_widget(CertificatesButton())
        self.add_widget(StatisticsButton())
