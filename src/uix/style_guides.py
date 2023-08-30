from dataclasses import dataclass
from kivy.core.window import Window  # type: ignore
import kivy.metrics as metrics
from typing import cast


__all__ = ["Sizes"]


@dataclass(init=False, frozen=True)
class Sizes:
    """Valores de tamanho de objetos, margens, bordas, etc."""

    @dataclass(init=False, frozen=True)
    class Nav:
        width = 70
        border_width = 3

        button_width = 60
        button_height = 60
        button_size = (button_width, button_height)
        button_margin = 10

    @dataclass(init=False, frozen=True)
    class Page:
        @classmethod
        def width(cls) -> int:
            """Largura da página."""
            return cast(int, Window.width) - (Sizes.Nav.width + Sizes.Nav.border_width)

        @classmethod
        def x(cls) -> int:
            """Posição X da página."""
            return Sizes.Nav.width + Sizes.Nav.border_width

        @dataclass(init=False, frozen=True)
        class HomePage:
            section_max_card_summed_width = 0.7  # porcentagem
            section_max_cards_per_row = 2
            title_margin_x = 10
            title_margin_y = 10
            title_separator_margin = metrics.pt(3)

            margin_between_cards = 10
            # largura maxima calculada com a regra de 3
            # largura mínima       -> altura mínima
            # largura atual/máxima -> x
            card_min_width = 250
            card_max_width = 400
            card_min_height = 80
