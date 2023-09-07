"""Classes base para outras classes relevantes para a construção da página de seleção e
processamento das planilhas."""

from kivy.uix.relativelayout import RelativeLayout

from src.uix.style_guides import Sizes

__all__ = ["FileSelectSection"]


class FileSelectSection(RelativeLayout):
    """Seção da página que separa elementos em categorias ou funções."""

    def render_frame(self) -> None:
        """Calculos feitos a cada frame."""
        self.width = Sizes.Page.width()
