from kivy.uix.boxlayout import BoxLayout

from src.utils.io import loadkv

__all__ = ["Page"]

loadkv("pages")


class Page(BoxLayout):
    identifier: str
