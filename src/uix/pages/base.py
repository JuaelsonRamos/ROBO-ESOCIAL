"""Classes base comuns a todas as páginas."""

from kivy.uix.boxlayout import BoxLayout

from src.utils.io import loadkv

__all__ = ["Page"]

loadkv("pages")


class Page(BoxLayout):
    """Classe base para a definição de novas páginas."""

    identifier: str
