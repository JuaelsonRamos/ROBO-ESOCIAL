import kivy
from kivy.config import Config
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from os.path import join
from src.utils.io import PastasProjeto, getkv

__all__ = ["BaseLayout", "CoralApp"]

kivy.require("2.2.1")


class BaseLayout(BoxLayout):
    orientation = "horizontal"


class CoralApp(App):
    kv_directory = PastasProjeto.kvlang
    kv_file = getkv("app")

    def build(self):
        Config.read(join(PastasProjeto.config, "kivyconf.ini"))
        return BaseLayout()
