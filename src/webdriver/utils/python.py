""" Operações úteis e genérias relacionadas a linguagem Python."""

import sys

__all__ = ["DEBUG", "string_multilinha"]

DEBUG: bool = hasattr(sys, "gettrace") and (sys.gettrace() is not None)
""" Se o programa está sendo executado em modo de Debug."""


def string_multilinha(texto: str) -> str:
    """Pega uma string gerada usando aspas triplas que tem quebras de linha e a transforma em uma
    linha só."""
    texto = texto.strip()
    return " ".join([linha.strip() for linha in texto.split("\n") if len(linha.strip()) > 0])
