from __future__ import annotations

import random

from typing import Any


def change_random(data: list[Any], value: Any):
    other = data.copy()
    rand_index = random.randrange(0, len(other))
    other[rand_index] = value
    return other
