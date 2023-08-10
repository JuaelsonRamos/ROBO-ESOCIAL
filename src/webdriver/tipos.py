""" Definições de tipos personalizados que não dependem de nenhum outro módulo dentro da própria
code base."""

from typing import NewType, Tuple, TypeAlias

__all__ = ["CelulaVazia", "CelulaVaziaType", "Float", "Int", "SeletorHTML"]

SeletorHTML: TypeAlias = Tuple[str, str]
CelulaVaziaType = NewType("CelulaVaziaType", float)
CelulaVazia: CelulaVaziaType = CelulaVaziaType(float("nan"))

# Tipos do cython são definidos na hora da compilação
Int = NewType("Int", int)
Float = NewType("Float", float)
