from kivy.uix.relativelayout import RelativeLayout

from src.uix.style_guides import Sizes

__all__ = ["FileSelectSection"]


class FileSelectSection(RelativeLayout):
    def render_frame(self) -> None:
        self.width = Sizes.Page.width()
