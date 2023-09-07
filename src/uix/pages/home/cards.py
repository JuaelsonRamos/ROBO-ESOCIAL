"""Cartões que representam páginas."""

from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.properties import StringProperty  # type: ignore # pylint: disable=no-name-in-module
from typing import Dict, Any

from src.utils.io import geticon
from src.uix.style_guides import Colors

__all__ = [
    "CertificatesCard",
    "EventsCard",
    "FileSelectCard",
    "InfoCard",
    "PageCard",
    "PageCardIcon",
    "StatisticsCard",
]


class PageCardIcon(Image):
    """Ícone referente da respectiva página."""


class PageCard(Button):
    """Cartão que representa uma página."""

    icon_path = StringProperty(geticon("icone_desconhecido"))

    kv_opts: Dict[str, Any] = dict(size_hint=(None, None))

    def on_press(self):
        """Calculos realizados quando o botão é clicado."""
        self.background_color_obj.rgba = Colors.gray
        self.color = self.icon.color = self.shadow_color_obj.rgba = Colors.light_red

    def on_release(self):
        """Cálculos realizados quando o clique é solto."""
        self.background_color_obj.rgba = Colors.white
        self.color = self.icon.color = self.shadow_color_obj.rgba = Colors.black
        self.button.state = "down"

    def __init__(self, button: Button, **kw: Any):
        self.kv_opts.update(kw)
        super().__init__(**self.kv_opts)

        self.button = button
        self.icon = PageCardIcon(source=self.icon_path)
        self.add_widget(self.icon)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]
        self.shadow_color_obj = self.canvas.before.get_group("shadow_color")[0]


class FileSelectCard(PageCard):
    """Cartão de página de seleção de arquivos."""

    text = "Selecionar planilhas para\nserem processadas"
    icon_path = geticon("planilha")


class CertificatesCard(PageCard):
    """Cartão da página de gerenciamento de certificados."""

    text = "Gerencie certificados\ndigitais (procurações)"
    icon_path = geticon("certificado")


class EventsCard(PageCard):
    """Cartão da página de observação de eventos."""

    text = "Visualize ações realizadas\npelo programa"
    icon_path = geticon("eventos")


class StatisticsCard(PageCard):
    """Cartão da página de visualização de estatisticas de uso do programa."""

    text = "Estatísticas de uso e\nprocessamento de planilhas"
    icon_path = geticon("estatisticas")


class InfoCard(PageCard):
    """Cartão da página de iformações do programa."""

    text = "Sobre"
    icon_path = geticon("info")
