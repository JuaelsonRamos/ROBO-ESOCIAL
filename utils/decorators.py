from __future__ import annotations

import abc
import sys
import inspect


def block(function):
    """Decorador de transforma uma definição de função em um
    bloco de código anônimo. A função não será definida e
    será imediatamente executada."""
    function()


def singleton(cls):
    assert not inspect.isbuiltin(cls)
    assert inspect.getmodule(cls) is not sys.modules['builtins']
    assert inspect.isclass(cls)
    assert abc.ABCMeta not in cls.__bases__
    assert abc.ABC not in cls.__bases__
    assert callable(cls)
    return cls()
