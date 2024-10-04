"""Barra de navegação."""

from kivy.uix.togglebutton import ToggleButton
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.core.window import Window  # type: ignore
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty  # type: ignore
from kivy.clock import Clock
from kivy.uix.widget import Widget
from typing import Any, Dict, List

from src.local.types import Int
from src.uix.pages.file_select import FileSelectPage
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
            y = Window.height - (Sizes.Nav.button_margin * order + self.height * order)
            if y != self.y:
                self.y = y
        else:
            y = Sizes.Nav.button_margin * order + (self.height * (order - 1))
            if y != self.y:
                self.y = y

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

        w, h = self.shadow_obj.size
        self.shadow_obj.size = (
            w + Sizes.Nav.on_pressed_border_width,
            h + Sizes.Nav.on_pressed_border_width,
        )

        self.shadow_color_obj.rgba = self.icon.color = Colors.light_red

    def _release(self) -> None:
        self.app.remove_widget(self.page_instance)
        self.shadow_obj.size = self.background_obj.size
        self.shadow_color_obj.rgba = self.icon.color = Colors.black

    def _double_check_states(self) -> None:
        buttons: List[ToggleButton] = ToggleButtonBehavior.get_widgets("nav_button")
        for down in (b for b in buttons if b.state == "down" and not isinstance(b, type(self))):
            down.state = "normal"
        # Obrigatório de acordo com a documentação do Kivy para
        # não impedir o objeto de ser garbage collected.
        del buttons

    def on_press(self) -> None:
        if self.state == "down":
            return None
        self.state = "down"

    def on_state(self, widget: Widget, value: str) -> None:
        if value == "down":
            self._press()
            self._double_check_states()
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
        self.background_obj = self.canvas.before.get_group("background")[0]
        self.shadow_obj = self.canvas.before.get_group("shadow")[0]

        Clock.schedule_interval(self.render_frame, 1 / 60)


class HomeButton(NavButton):
    """Botão para a página de seleção de páginas."""

    order_position_top = 1
    icon_path = geticon("home")
    first_state_set = False

    def render_frame(self, delta: float) -> None:
        if self.background_obj.pos != (0, 0) and not self.first_state_set:
            # De outra maneira o estado seria definido antes da posição real do
            # retângulo estar disponível. Assim, a posição do retângulo seria
            # definida pelo evento de estado e depois sobrescrevida pelo KV.
            self.state = "down"
            self.first_state_set = True
        super().render_frame(delta)

    def __init__(self, app: Widget, *button_instances: ToggleButton, **kw: Any) -> None:
        self.page_buttons = button_instances
        self.page_instance = HomePage(*self.page_buttons)
        super().__init__(app, **kw)


class FileSelectButton(NavButton):
    """Botão para a página de seleção de planilhas."""

    order_position_top = 2
    icon_path = geticon("planilha")

    def __init__(
        self,
        app: Widget,
        to_process_queue: object,
        started_event: object,
        progress_values: object,
        **kw: Any,
    ) -> None:
        self.page_instance = FileSelectPage(
            to_process_queue, started_event, progress_values
        )
        super().__init__(app, **kw)


class CertificatesButton(NavButton):
    """Botão para a página de gerenciamento de certificados."""

    order_position_top = 3
    icon_path = geticon("certificado")
    page_instance = Page()


class EventsButton(NavButton):
    """Botão para a página de log de eventos do processamento da planilha."""

    order_position_top = 4
    icon_path = geticon("eventos")
    page_instance = Page()


class StatisticsButton(NavButton):
    """Botão para a página de visualização de estatísticas sobre processamento das planilhas."""

    order_position_top = 5
    icon_path = geticon("estatisticas")
    page_instance = Page()


class InfoButton(NavButton):
    """Botão para a página de informações e configurações."""

    order_position_bottom = 1
    icon_path = geticon("info")
    page_instance = Page()


class Nav(FloatLayout):
    """Barra de navegação."""

    def __init__(
        self,
        app: Widget,
        to_process_queue: object,
        started_event: object,
        progress_values: object,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        buttons = [
            # ordem de definição de acordo com a classe HomePage
            EventsButton(app),
            FileSelectButton(
                app, to_process_queue, started_event, progress_values
            ),
            StatisticsButton(app),
            CertificatesButton(app),
            InfoButton(app),
        ]
        home = HomeButton(app, *buttons)

        self.add_widget(home)
        for b in home.page_buttons:
            self.add_widget(b)
