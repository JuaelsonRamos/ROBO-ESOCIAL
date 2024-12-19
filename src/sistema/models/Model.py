from __future__ import annotations

from dataclasses import asdict, astuple, dataclass, fields, replace
from typing import Any

from pydantic import ConfigDict, TypeAdapter


_adapters_registry: dict[type, TypeAdapter] = {}


@dataclass
class Model:
    def type_adapter(self) -> TypeAdapter:
        T = type(self)
        if T not in _adapters_registry:
            _adapters_registry[T] = TypeAdapter(T, config=ConfigDict(strict=False))
        return _adapters_registry[T]

    def astuple(self):
        return astuple(self)

    def asdict(self):
        return asdict(self)

    def replace(self, /, **changes):
        """Return new Model with modified fields denoted by `**changes`."""
        return replace(self, **changes)

    def fields(self):
        return fields(self)

    def __getitem__(self, name: str, /) -> Any:
        try:
            return getattr(self, name)
        except AttributeError as err:
            raise IndexError(err)
