from __future__ import annotations

from typing import Any


def isiterable(obj: Any) -> bool:
    # SEE https://stackoverflow.com/questions/1952464/python-how-to-determine-if-an-object-is-iterable
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True
