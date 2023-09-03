"""Barra de navegação."""

from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window  # type: ignore
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty  # type: ignore
from kivy.clock import Clock
from kivy.uix.widget import Widget
from typing import Any, Dict

from src.local.types import Int
from src.utils.io import geticon, loadkv
from src.uix.style_guides import Colors, Sizes
from src.uix.pages.home import HomePage
from src.uix.pages.base import Page

__all__ = [
    "CertificatesButton",
    "EventsButton",
    "FileSelectButton",
    "HomeButton",
    "InfoButton",
    "Nav",
    "NavButton",
    "NavButtonIcon",
    "StatisticsButton",
]

loadkv("nav")


class NavButtonIcon(Image):
    pass


class NavButton(ToggleButton):
    """Botão da barra de navegação de páginas."""

    icon_path = StringProperty(geticon("icone_desconhecido"))
    page_instance: Page

    order_position_top = Int(0)
    order_position_bottom = Int(0)

    kv_opts: Dict[str, Any] = dict(size=(60, 60), size_hint=(None, None))

    def _calc_y_nocheck(self) -> None:
        order = self.order_position_bottom or self.order_position_top
        if self.order_position_top:
            self.y = Window.height - (Sizes.Nav.button_margin * order + self.height * order)
        else:
            self.y = Sizes.Nav.button_margin * order + (self.height * (order - 1))

    def _calc_y(self) -> None:
        if self.order_position_bottom > 0 and self.order_position_top > 0:
            raise ValueError(
                "A button can only be either on top or on bottom. A position order was specified for both top and bottom."
            )
        elif self.order_position_bottom < 0 or self.order_position_top < 0:
            raise ValueError("A position order can't be negative.")

        self._calc_y_nocheck()

    def _calc_dimensions(self) -> None:
        self.icon.center_x = self.center_x
        self.icon.center_y = self.center_y

    def render_frame(self, delta: float) -> None:
        """Realizar cálculos que precisam ser feitos a cada frame.

        :param delta: Variação de tempo.
        """
        self._calc_y_nocheck()
        self._calc_dimensions()

    def _press(self) -> None:
        self.app.add_widget(self.page_instance)
        self.background_color_obj.rgba = Colors.black
        self.shadow_color_obj.rgba = self.icon.color = Colors.white

    def _release(self) -> None:
        self.app.remove_widget(self.page_instance)
        self.background_color_obj.rgba = Colors.white
        self.shadow_color_obj.rgba = self.icon.color = Colors.black

    def on_press(self) -> None:
        if self.state == "down":
            return None
        self.state = "down"

    def on_state(self, widget, value) -> None:
        if value == "down":
            self._press()
        else:
            self._release()

    def __init__(self, app: Widget, **kw: Any):
        self.app = app
        self.kv_opts.update(kw)
        super().__init__(**self.kv_opts)
        self._calc_y()

        self.icon = NavButtonIcon(source=self.icon_path)
        self.add_widget(self.icon)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]
        self.shadow_color_obj = self.canvas.before.get_group("shadow_color")[0]

        Clock.schedule_interval(self.render_frame, 1 / 60)


class HomeButton(NavButton):
    """Botão para a página de seleção de páginas."""

    order_position_top = 1
    icon_path = geticon("home")
    page_instance = HomePage()

    def __init__(self, app: Widget, **kw: Any) -> None:
        super().__init__(app, **kw)
        self.state = "down"


class FileSelectButton(NavButton):
    """Botão para a página de seleção de planilhas."""

    order_position_top = 2
    icon_path = geticon("planilha")


class CertificatesButton(NavButton):
    """Botão para a página de gerenciamento de certificados."""

    order_position_top = 3
    icon_path = geticon("certificado")


class EventsButton(NavButton):
    """Botão para a página de log de eventos do processamento da planilha."""

    order_position_top = 4
    icon_path = geticon("eventos")


class StatisticsButton(NavButton):
    """Botão para a página de visualização de estatísticas sobre processamento das planilhas."""

    order_position_top = 5
    icon_path = geticon("estatisticas")


class InfoButton(NavButton):
    """Botão para a página de informações e configurações."""

    order_position_bottom = 1
    icon_path = geticon("info")


class Nav(FloatLayout):
    """Barra de navegação."""

    def __init__(self, app: Widget, **kwargs: Any):
        super().__init__(**kwargs)
        self.add_widget(HomeButton(app))
        self.add_widget(InfoButton(app))
        self.add_widget(EventsButton(app))
        self.add_widget(FileSelectButton(app))
        self.add_widget(CertificatesButton(app))
        self.add_widget(StatisticsButton(app))
