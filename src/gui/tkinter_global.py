from __future__ import annotations

from src.exc import Tkinter

from tkinter import ttk
from typing import Any, Final, Generator

import sqlalchemy


# pyright: reportAttributeAccessIssue=false, reportAssignmentType=false


class TkinterGlobalMeta(type):
    """
    Class to allow methods that mess with property state using super() objects, since
    class objects are instances of metaclasses, and 'metaassigning' (I invented this
    term) requires the called setter to be contained in an instance of some sort.

    Event though the setter was being called after instantiation of the regular class,
    defining these methods in a metaclass fixed the issue. So, yeah.
    """

    __slots__ = ()

    def __getattr__(self, name: str, /) -> Any:
        if name not in self.__slots__:
            raise Tkinter.GlobalUnknown(name)
        if getattr(super(), name, None) is None:
            raise Tkinter.GlobalUndefined(name)
        return getattr(super(), name)

    def __getitem__(self, key: str, /) -> Any:
        return self.__getattr__(key)

    def __setattr__(self, name: str, value: Any, /) -> None:
        try:
            if getattr(super(), name, None) is not None:
                raise Tkinter.GlobalAssigned(name)
        except Tkinter.GlobalUndefined:
            pass  # exist but not yet assigned
        except Tkinter.GlobalUnknown as err:
            # forced expressiveness, announce that it may raise!!
            raise err
        setattr(super(), name, value)

    def __setitem__(self, key: str, value: Any, /) -> None:
        return self.__setattr__(key, value)

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
        except (AttributeError, Tkinter.GlobalUnknown, Tkinter.GlobalUndefined):
            return False
        except Tkinter.GlobalAssigned:
            return True
        else:
            return True


class TkinterGlobalType(metaclass=TkinterGlobalMeta):
    __slots__ = ('style', 'sqlite')

    style: ttk.Style
    sqlite: sqlalchemy.Engine


TkinterGlobal: Final[TkinterGlobalType] = TkinterGlobalType()
