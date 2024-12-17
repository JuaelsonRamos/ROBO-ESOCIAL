from __future__ import annotations

from tkinter import ttk
from typing import Any, Final, Generator

import sqlalchemy


class TkinterGlobalUndefined(NotImplementedError):
    def __init__(self, name: str, /) -> None:
        super().__init__(f'property {name=} has not yet been assigned')


class TkinterGlobalAssigned(RuntimeError):
    def __init__(self, name: str, /) -> None:
        super().__init__(f'property {name=} has already been assigned once')


class TkinterGlobalType:
    __slots__ = ('style', 'sqlite')

    style: ttk.Style
    sqlite: sqlalchemy.Engine

    def __getattr__(self, name: str, /) -> Any:
        if getattr(super(), name, None) is None:
            raise TkinterGlobalUndefined(name)
        return getattr(super(), name)

    def __getitem__(self, key: str, /) -> Any:
        return self.__getattr__(key)

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name) or getattr(super(), name) is not None:
            raise TkinterGlobalAssigned(name)

    def fields(self) -> tuple[str, ...]:
        return self.__slots__

    def items(self) -> Generator[tuple[str, Any | None], None, None]:
        for prop in self.__slots__:
            yield (prop, getattr(super(), prop, None))

    def has(self, name: str, /) -> bool:
        """Has attr and is initialized."""
        try:
            if getattr(super(), name) is None:
                return False
        except AttributeError:
            return False
        else:
            return True


TkinterGlobal: Final[TkinterGlobalType] = TkinterGlobalType()
