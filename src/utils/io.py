from dataclasses import dataclass
from os.path import abspath, dirname, join
from kivy.lang import Builder

from src.local.types import KvFile

__all__ = ["PastasProjeto", "geticon", "getkv", "loadkv"]


@dataclass(init=False, frozen=True)
class PastasProjeto:
    """Pastas relacionadas ao próprio projeto (código fonte).

    :final:
    """

    root: str = abspath(join(dirname(__file__), "..", ".."))
    assets: str = join(root, "assets")
    config: str = join(root, "config")
    kvlang: str = join(root, "src", "kv")
    uix_assets: str = join(root, "assets", "uix")
    uix_icons: str = join(root, "assets", "uix", "icons")


def loadkv(name: str) -> KvFile:
    """Carrega arquivo kv baseado em seu nome sem extensão."""
    basename: str = "{}.kv".format(name)
    path: str = join(PastasProjeto.kvlang, basename)
    return KvFile(
        root_widget=Builder.load_file(path), path=path, name=name, basename=basename  # type: ignore
    )


def getkv(name: str) -> str:
    """Pegar caminho para arquivo KV baseado no nome sem extensão."""
    return join(PastasProjeto.kvlang, "{}.kv".format(name))


def geticon(name: str) -> str:
    """Pegar caminho para ícone que funcione no Kivy."""
    return join(PastasProjeto.uix_icons, "{}.png".format(name))
