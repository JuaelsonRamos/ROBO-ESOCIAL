"""Definições de tipos personalizados que não dependem de nenhum outro módulo dentro da própria code
base."""

from typing import NewType, Tuple, TypeAlias, NamedTuple
import pandas as pd


__all__ = ["CelulaVazia", "CelulaVaziaType", "PlanilhaPronta", "SeletorHTML"]

SeletorHTML: TypeAlias = Tuple[str, str]
CelulaVaziaType = NewType("CelulaVaziaType", float)
CelulaVazia: CelulaVaziaType = CelulaVaziaType(float("nan"))

PlanilhaPronta = NamedTuple(
    "PlanilhaPronta", [("dataframe", pd.DataFrame), ("name", str), ("original_path", str)]
)
