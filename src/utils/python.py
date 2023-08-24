"""Operações úteis e genérias relacionadas a linguagem Python."""

import sys
from typing import Generic, Iterator, TypeVar
from dataclasses import dataclass, field

__all__ = ["DEBUG", "LoopState", "string_multilinha"]

DEBUG: bool = hasattr(sys, "gettrace") and (sys.gettrace() is not None)
"""Se o programa está sendo executado em modo de Debug."""

_T = TypeVar("_T")


def string_multilinha(texto: str) -> str:
    """Pega uma string gerada usando aspas triplas que tem quebras de linha e a transforma em uma
    linha só."""
    texto = texto.strip()
    return " ".join([linha.strip() for linha in texto.split("\n") if len(linha.strip()) > 0])


@dataclass
class LoopState(Generic[_T]):
    """Estado do um loop que você quer identificar melhor.

    :param iterator: Iterator que viaja pelos objetos que você deseja.
    """

    iterator: Iterator[_T]
    locked: bool = field(init=False, default=False)

    def lock(self) -> None:
        """Abstração para ``loop.locked = True``"""
        if not self.locked:
            self.locked = True

    def unlock(self) -> None:
        """Abstração para ``loop.locked = False``"""
        if self.locked:
            self.locked = False
