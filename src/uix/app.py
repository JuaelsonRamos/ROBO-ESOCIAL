"""Definição da aplicação."""

import kivy
from kivy.config import Config
from kivy.app import App
from os.path import join
from src.utils.io import PastasProjeto, loadkv
from src.uix.nav import Nav

__all__ = ["CoralApp"]

kivy.require("2.2.1")


class CoralApp(App):
    """Definição da aplicação."""

    def build(self):
        Config.read(join(PastasProjeto.config, "kivyconf.ini"))
        base = loadkv("app").root_widget
        if not base:
            raise ValueError("No root widget returned from kv file. Can't creat app root widget.")
        base.add_widget(Nav())
        return base
