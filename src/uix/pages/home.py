from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.properties import StringProperty  # type: ignore
from kivy.clock import Clock
from typing import Any, List, Dict, cast
import math

from src.uix.pages.base import Page
from src.uix.style_guides import Sizes, Colors
from src.utils.io import loadkv, geticon

__all__ = [
    "CertificatesCard",
    "EventsCard",
    "FileSelectCard",
    "HomePage",
    "ManagementSection",
    "PageCard",
    "PageCardIcon",
    "Section",
    "SectionTitle",
    "StatisticsCard",
    "StatisticsSection",
]

loadkv("home")


class PageCardIcon(Image):
    pass


class PageCard(Button):
    icon_path = StringProperty(geticon("icone_desconhecido"))

    kv_opts: Dict[str, Any] = dict(size_hint=(None, None))

    def on_press(self):
        self.background_color_obj.rgba = Colors.black
        self.color = self.icon.color = self.shadow_color_obj.rgba = Colors.white

    def on_release(self):
        self.background_color_obj.rgba = Colors.white
        self.color = self.icon.color = self.shadow_color_obj.rgba = Colors.black

    def __init__(self, **kw: Any):
        self.kv_opts.update(kw)
        super().__init__(**self.kv_opts)

        self.icon = PageCardIcon(source=self.icon_path)
        super().add_widget(self.icon)
        self.background_color_obj = self.canvas.before.get_group("background_color")[0]
        self.shadow_color_obj = self.canvas.before.get_group("shadow_color")[0]


class FileSelectCard(PageCard):
    text = "Selecionar planilhas para\nserem processadas"
    icon_path = geticon("planilha")


class CertificatesCard(PageCard):
    text = "Gerencie certificados\ndigitais (procurações)"
    icon_path = geticon("certificado")


class EventsCard(PageCard):
    text = "Visualize ações realizadas\npelo programa"
    icon_path = geticon("eventos")


class StatisticsCard(PageCard):
    text = "Estatísticas de uso e\nprocessamento de planilhas"
    icon_path = geticon("estatisticas")


class SectionTitle(Label):
    pass


class Section(RelativeLayout):
    title: str = ""
    cards: List[PageCard] = []

    def _card_dimensions(self, card: PageCard, index: int) -> None:
        """Calcula posição e tamanho do card.

        :param card: Widget do card.
        :param index: Número da order de aparição daquele card (primeiro = 0, segundo = 1, etc).
        """
        row_num = math.ceil((index + 1) / Sizes.Page.HomePage.section_max_cards_per_row)
        row_amount = math.ceil(self.card_amount / Sizes.Page.HomePage.section_max_cards_per_row)
        cards_in_row = (
            self.card_amount - (row_amount - 1) * Sizes.Page.HomePage.section_max_cards_per_row
        )
        card_row_pos = (index + 1) - (row_num - 1) * Sizes.Page.HomePage.section_max_cards_per_row

        # TAMANHO...
        margin_sum = Sizes.Page.HomePage.margin_between_cards * (cards_in_row - 1)
        min_total_card_width_sum = Sizes.Page.HomePage.card_min_width * cards_in_row + margin_sum
        max_total_width = Sizes.Page.width() * Sizes.Page.HomePage.section_max_card_summed_width

        if min_total_card_width_sum > max_total_width:
            # Se a janela for diminuída demais e largura mínima ocupável for maior que o espaço
            # disponível, use o tamanho mínimo do card, ao envés de diminuir ele ainda mais.
            card.width = Sizes.Page.HomePage.card_min_width
        elif (
            width := (max_total_width - margin_sum) / cards_in_row
        ) < Sizes.Page.HomePage.card_max_width:
            card.width = width
        else:
            card.width = Sizes.Page.HomePage.card_max_width

        # POSIÇÃO...
        first_of_row_x_pos = (
            Sizes.Page.width()
            - (
                cast(int, card.width) * cards_in_row
                + Sizes.Page.HomePage.margin_between_cards * (card_row_pos - 1)
            )
        ) / 2

        self.title_widget.y = (
            row_amount * card.height
            + (row_amount - 1) * Sizes.Page.HomePage.margin_between_cards
            + Sizes.Page.HomePage.title_separator_margin * 3
        )

        self.title_widget.x = Sizes.Page.HomePage.margin_between_cards * 1.5

        title_sep = self.title_widget.canvas.get_group("title_separator")[0]
        title_sep.size = (
            Sizes.Page.width() - self.title_widget.x * 2,
            title_sep.size[1],
        )
        title_sep.pos = (self.title_widget.x, title_sep.pos[1])

        if first_of_row_x_pos <= self.title_widget.x:
            # Se a largura da página diminuir demais, posicione os cards de acordo com o título
            card.x = self.title_widget.x + (
                card.width + Sizes.Page.HomePage.margin_between_cards * 1.5
            ) * (card_row_pos - 1)
        else:
            card.x = first_of_row_x_pos + (
                card.width + Sizes.Page.HomePage.margin_between_cards * 1.5
            ) * (card_row_pos - 1)

        card.y = cast(int, card.height) * (
            row_amount - row_num
        ) + Sizes.Page.HomePage.margin_between_cards * (row_amount - row_num)

        # CENTRALIZAR TUDO...
        ocupied_height = cast(float, self.title_widget.y + self.title_widget.height)
        difference = cast(float, self.height / 2 - ocupied_height / 2)
        if ocupied_height >= self.height:
            self.title_widget.y += Sizes.Page.HomePage.margin_between_cards
            card.y += Sizes.Page.HomePage.margin_between_cards
        else:
            self.title_widget.y += difference
            card.y += difference

        # ICONE...
        card.icon.center_y = card.y + card.height / 2
        card.icon.center_x = card.x + Sizes.Page.HomePage.card_icon_area_width / 2

        # TEXTO...
        card.text_size = card.size
        card.padding = (Sizes.Page.HomePage.card_icon_area_width, 0, 0, 0)

    def render_frame(self) -> None:
        for i, card in enumerate(self.cards):
            self._card_dimensions(card, i)

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self.title_widget = SectionTitle(text=self.title)
        self.card_amount = len(self.cards)

        self.add_widget(self.title_widget)
        for c in self.cards:
            self.add_widget(c)


class ManagementSection(Section):
    title = "Gerenciamento"
    cards = [FileSelectCard(), CertificatesCard(), FileSelectCard(), CertificatesCard()]


class StatisticsSection(Section):
    title = "Estatísticas"
    cards = [EventsCard(), StatisticsCard()]


class HomePage(Page):
    """Página de seleção de páginas."""

    identifier = "home"

    def render_frame(self, delta: float) -> None:
        for section in self.children:
            section.height = self.height / len(self.children)
            section.render_frame()

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self.add_widget(ManagementSection())
        self.add_widget(StatisticsSection())

        Clock.schedule_interval(self.render_frame, 1 / 60)
