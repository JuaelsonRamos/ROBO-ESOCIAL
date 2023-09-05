from dataclasses import dataclass
from kivy.core.window import Window  # type: ignore
import kivy.metrics as metrics
from typing import cast, Tuple


__all__ = ["Colors", "Sizes", "rgb", "rgba"]


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

        icon_max_size = 50

        shadow_offset = 1.5
        on_pressed_border_width = 3

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
            # Largura maxima calculada com a regra de 3:
            # largura minima        -> altura minima
            # largura atual/maxima  -> x
            # Com x sendo min_height <= x <= max_height
            card_min_width = 250
            card_max_width = 400
            card_min_height = 80
            card_max_height = 100

            card_icon_area_width = 80
            card_icon_max_size = 60


def rgb(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Converte um valor RGB onde cada valor é ``0 <= x <= 255`` para um valor equivalente em
    porcentagem no formato ``0 <= x <= 1``.

    :param r: Valor para a cor vermelho entre 0 e 255.
    :param g: Valor para a cor verde entre 0 e 255.
    :param b: Valor para a cor azul entre 0 e 255.
    :return: Tuple com os valores convertidos.
    """
    if any(value > 255 or value < 0 for value in [r, g, b]):
        raise ValueError("Valor de cor deve estar entre e incluindo 0 e 255")
    return cast(Tuple[float, float, float], tuple(value / 255 for value in [r, g, b]))


def rgba(r: float, g: float, b: float, a: float) -> Tuple[float, float, float, float]:
    """Equivalente a função :func:`rgb`, exceto que um valor é adicionado ao final do tuple gerado
    referente ao alpha (transparência) que já deve estar no formato ``0 <= x <= 255``.

    :param r: Valor para a cor vermelho entre 0 e 255.
    :param g: Valor para a cor verde entre 0 e 255.
    :param b: Valor para a cor azul entre 0 e 255.
    :param a: Valor do nível de transparência entre 0 e 1.
    :return: Tuple com os valores convertidos.
    """
    if a > 1 or a < 0:
        raise ValueError("Transparencia deve estar entre e incluindo 0 e 1")
    return cast(Tuple[float, float, float, float], (*rgb(r, g, b), a))


@dataclass(init=False, frozen=True)
class Colors:
    main_background = rgba(239, 239, 239, 1)
    red = rgba(204, 36, 29, 1)
    light_red = rgba(242, 32, 23, 1)
    yellow = rgba(255, 191, 0, 1)
    dark_yellow = rgba(255, 186, 0, 1)
    green = rgba(26, 152, 26, 1)
    white = rgba(226, 226, 226, 1)
    black = rgba(68, 68, 68, 1)
    gray = rgba(210, 210, 210, 1)
    page_card_outer_shadow = rgba(*black[:-1], 0.75)
