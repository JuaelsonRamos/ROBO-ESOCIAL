from __future__ import annotations

from dataclasses import dataclass
from typing import cast


def padding(
    *,
    left: int = 0,
    right: int = 0,
    top: int = 0,
    bottom: int = 0,
    horizontal: int = 0,
    vertical: int = 0,
):
    if horizontal and (right or left):
        raise ValueError(
            "'horizontal' is specified, neither 'left' nor 'right' can be specified"
        )
    if vertical and (top or bottom):
        raise ValueError(
            "'horizontal' is specified, neither 'left' nor 'right' can be specified"
        )

    padding = [left, top, right, bottom]
    if horizontal:
        padding[0] = padding[2] = horizontal
    if vertical:
        padding[1] = padding[3] = vertical

    return cast(tuple[int, int, int, int], tuple(padding))


@dataclass(frozen=True, init=False)
class length:
    @classmethod
    def centimiter(cls, size: int = 0) -> str:
        return f'{size}c'

    @classmethod
    def point(cls, size: int = 0) -> str:
        return f'{size}p'

    @classmethod
    def inch(cls, size: int = 0) -> str:
        return f'{size}i'

    @classmethod
    def milimiter(cls, size: int = 0) -> str:
        return f'{size}m'
