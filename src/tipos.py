""" Definições de tipos personalizados que não dependem de nenhum outro módulo dentro da própria
code base."""

from typing import NewType, Tuple
import cython

__all__ = ["CelulaVazia", "CelulaVaziaType", "Float", "Int", "SeletorHTML"]

SeletorHTML = NewType("SeletorHTML", Tuple[str, str])
CelulaVaziaType = NewType("CelulaVaziaType", float)
CelulaVazia: CelulaVaziaType = CelulaVaziaType(float("nan"))

# Tipos do cython são definidos na hora da compilação
Int = NewType("Int", cython.long)  # pylint: disable=no-member # type: ignore
Float = NewType("Float", cython.double)  # pylint: disable=no-member # type: ignore
