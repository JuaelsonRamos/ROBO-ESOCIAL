from __future__ import annotations

from typing import Any, NamedTuple, Self


class _int_maybe_float(int):
    def __new__(cls, x: Any) -> Self:
        instance = super().__new__(x)
        cls.__float_self = float(x)
        return instance

    def asfloat(self) -> float:
        return self.__float_self


class _integer_namespace(NamedTuple):
    MIN: _int_maybe_float
    MAX: _int_maybe_float


INT32 = _integer_namespace(
    MIN=_int_maybe_float(-(2**31)),
    MAX=_int_maybe_float(2**31 - 1),
)

UINT32 = _integer_namespace(
    MIN=_int_maybe_float(0),
    MAX=_int_maybe_float(2**32),
)
