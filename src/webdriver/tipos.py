"""Definições de tipos personalizados que não dependem de nenhum outro módulo dentro da própria code
base."""

from typing import NewType, Tuple, TypeAlias, NamedTuple
import pandas as pd


__all__ = [
    "ArquivoPlanilha",
    "CelulaVazia",
    "CelulaVaziaType",
    "Float",
    "Int",
    "PlanilhaPronta",
    "SeletorHTML",
]

SeletorHTML: TypeAlias = Tuple[str, str]
CelulaVaziaType = NewType("CelulaVaziaType", float)
CelulaVazia: CelulaVaziaType = CelulaVaziaType(float("nan"))


class Int(int):
    """Classe para forçar a diferenciação entre int e float."""


class Float(float):
    """Classe para forçar a diferenciação entre int e float."""


PlanilhaPronta = NamedTuple(
    "PlanilhaPronta", [("dataframe", pd.DataFrame), ("name", str), ("original_path", str)]
)

ArquivoPlanilha = NamedTuple(
    "ArquivoPlanilha", [("isfile", bool), ("identifier", str), ("path", str)]
)
"""Registro de informações relevantes para a seleção de arquivos pré processamento."""
