import os
from dataclasses import dataclass
from os.path import abspath, dirname, join
from typing import NamedTuple

__all__ = ["PastasProjeto", "PastasSistema", "criar_pastas_de_sistema"]

PastasSistema = NamedTuple("PastasSistema",
    [("input", str), ("output", str), ("pronto", str), ("nao_excel", str)]
)(
    "C:\\SISTEMA_PLANILHAS",
    "C:\\SISTEMA_PLANILHAS_PROCESSADAS",
    "C:\\SISTEMA_PLANILHAS_ARQUIVADAS",
    "C:\\SISTEMA_LIXEIRA",
)


def criar_pastas_de_sistema() -> None:
    for pasta in PastasSistema:
        try:
            os.mkdir(pasta)
        except FileExistsError:
            pass


@dataclass(init=False, frozen=True)
class PastasProjeto:
    root: str = abspath(join(dirname(__file__), "..", ".."))
    assets: str = join(root, "assets")
