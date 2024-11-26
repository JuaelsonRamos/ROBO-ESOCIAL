from __future__ import annotations

import abc
import sys
import inspect

from typing import Any, Callable, TypeVar, cast


C = TypeVar('C', bound=Any)


def block(function: Callable[[], None]) -> None:
    """Decorador de transforma uma definição de função em um
    bloco de código anônimo. A função não será definida e
    será imediatamente executada."""
    function()


def singleton(cls: type[C]) -> C:
    assert not inspect.isbuiltin(cls)
    assert inspect.getmodule(cls) is not sys.modules['builtins']
    assert inspect.isclass(cls)
    assert abc.ABCMeta not in cls.__bases__
    assert abc.ABC not in cls.__bases__
    assert callable(cls)
    return cast(C, cls())
