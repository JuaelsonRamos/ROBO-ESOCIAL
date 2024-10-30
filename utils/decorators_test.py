from __future__ import annotations

from .decorators import block

import pytest


def test_block():
    class BlockExecuted(Exception):
        pass

    with pytest.raises(BlockExecuted):

        @block
        def anonymous_function():
            raise BlockExecuted()
