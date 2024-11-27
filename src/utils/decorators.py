from __future__ import annotations

from typing import Any, Callable, TypeVar


T = TypeVar('T', bound=Any)


def block(function: Callable[[], None]) -> None:
    """
    Decorador de transforma uma definição de função em um bloco de código anônimo.

    A função não será definida e será imediatamente executada.
    """
    function()

def value(func: Callable[[], T]) -> T:
    """Decorador que transforma função em variável com valor igual ao retornado."""
    return func()
