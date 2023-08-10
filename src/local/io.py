""" Operações genéricas relacionadas ao sistema de arquivos do sistema operacional."""

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
""" Lista de pastas do sistema que o programa utiliza."""

def criar_pastas_de_sistema() -> None:
    """ Cria as pastas que o programa vai utilizar para guardar dados importantes."""
    for pasta in PastasSistema:
        try:
            os.mkdir(pasta)
        except FileExistsError:
            pass


@dataclass(init=False, frozen=True)
class PastasProjeto:
    """ Pastas relacionadas ao próprio projeto (código fonte).

    :final:
    """
    root: str = abspath(join(dirname(__file__), "..", ".."))
    assets: str = join(root, "assets")
