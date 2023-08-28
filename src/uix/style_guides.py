from dataclasses import dataclass

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
