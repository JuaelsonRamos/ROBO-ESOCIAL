from __future__ import annotations


def block(function):
    """Decorador de transforma uma definição de função em um
    bloco de código anônimo. A função não será definida e
    será imediatamente executada."""
    function()
