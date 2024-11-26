from __future__ import annotations

from .decorators import block, singleton

import pytest

import abc
import inspect


# mypy: disable-error-code="arg-type, unreachable"


def test_block():
    class BlockExecuted(Exception):
        pass

    with pytest.raises(BlockExecuted):

        @block
        def anonymous_function():
            raise BlockExecuted()


def test_singleton():
    # NOTE Deve checar por builtins primeiro, pois builtins podem ser objetos variados,
    # causando uma série de falsos positivos. Além disso, para expressividade, é bom que
    # fique claro que builtins causam um erro.

    # Devem falhar por serem builtins!
    with pytest.raises(AssertionError):
        singleton(open)  # função
    with pytest.raises(AssertionError):
        singleton(filter)  # classe
    with pytest.raises(AssertionError):
        singleton(__import__)  # função

    with pytest.raises(AssertionError):

        @singleton
        def not_class(): ...

    with pytest.raises(AssertionError):

        @singleton
        class abstract_class(abc.ABC):
            pass

    try:

        @singleton
        class ShouldWork:
            pass

        assert not inspect.isclass(ShouldWork)
        assert hasattr(ShouldWork, '__class__')
        assert isinstance(ShouldWork, ShouldWork.__class__)
    except AssertionError:
        pytest.fail('declaração de classe deveria retornar instância anônima')
