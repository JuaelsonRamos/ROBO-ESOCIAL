__all__ = ["Float", "Int", "KvFile"]

from typing import NamedTuple
from kivy.uix.widget import Widget
from kivy.lang import Builder


class Int(int):
    """Classe para forçar a diferenciação entre int e float."""


class Float(float):
    """Classe para forçar a diferenciação entre int e float."""


_KvFileBase = NamedTuple(
    "_KvFileBase",
    [
        ("root_widget", Widget | None),
        ("path", str),
        ("name", str),
        ("basename", str),
    ],
)


class KvFile(_KvFileBase):
    """Informações relacionadas ao arquivo KV especificado."""

    def unload(self) -> None:
        """Descarrega todas as regras especificadas no arquivo KV."""
        Builder.unload_file(self.path)

    def has_widget(self) -> bool:
        """Retorna se um Widget root foi retornado do arquivo KV ou não."""
        return bool(self.root_widget)
