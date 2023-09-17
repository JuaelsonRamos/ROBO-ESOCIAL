"""Definição da aplicação."""

from typing import Any
import kivy
from kivy.app import App
from kivy.config import ConfigParser
from kivy.core.window import Window  # type: ignore
from os.path import join
from src.utils.io import PastasProjeto, loadkv
from src.uix.nav import Nav

__all__ = ["CoralApp"]

kivy.require("2.2.1")


class CoralApp(App):
    """Definição da aplicação."""

    def build_config(self, config: ConfigParser) -> None:
        config.read(join(PastasProjeto.config, "kivyconf.ini"))
        size = (config.getint("graphics", "width"), config.getint("graphics", "height"))
        Window.size = size
        Window.minimum_width, Window.minimum_height = size

    def build(self):
        base = loadkv("app").root_widget
        if not base:
            raise ValueError("No root widget returned from kv file. Can't creat app root widget.")

        base.add_widget(
            Nav(
                base,
                self.to_process_queue,
                self.started_event,
                self.progress_values,
            )
        )

        return base

    def __init__(
        self,
        to_process_queue: object,
        started_event: object,
        progress_values: object,
        **kw: Any,
    ):
        self.to_process_queue = to_process_queue
        self.started_event = started_event
        self.progress_values = progress_values
        super().__init__(**kw)
