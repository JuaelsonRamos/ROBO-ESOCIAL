from __future__ import annotations

from src.utils import isiterable

import random

from typing import Any, Iterable


def change_random(data: Iterable[Any], value: Any) -> list[Any]:
    assert not isinstance(data, str)
    assert isiterable(data)
    other = list(data)
    rand_index = random.randrange(0, len(other))
    other[rand_index] = value
    return other
