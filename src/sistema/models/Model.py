from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    NamedTupleMeta,# type: ignore
    SupportsIndex,
)

from pydantic import ConfigDict, TypeAdapter


# SEE typing.NamedTupleMeta implementation


class ModelMeta(NamedTupleMeta):
    __adapters: dict[type, TypeAdapter] = {}

    def __new__(cls, name, bases, attrs):
        nm_tpl = super().__new__(name, bases, attrs)
        if nm_tpl not in cls.__adapters:
            cls.__adapters[nm_tpl] = TypeAdapter(
                nm_tpl, config=ConfigDict(strict=False)
            )
        return nm_tpl

    def _type_adapter(self) -> TypeAdapter:
        return self.__adapters[self]




if TYPE_CHECKING:

    class Model:
        __adapters: ClassVar[dict[type, TypeAdapter]]

        @abstractmethod
        def _type_adapter(cls) -> TypeAdapter: ...

        @abstractmethod
        def __getitem__(self, name: str | slice | SupportsIndex, /) -> Any: ...

else:

    class Model(metaclass=ModelMeta):
        def __getitem__(self, name: str | slice | SupportsIndex, /) -> Any:
            if isinstance(name, str):
                try:
                    return getattr(self, name)
                except AttributeError as err:
                    raise IndexError(err)
            return self.__getitem__(name)
