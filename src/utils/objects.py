from __future__ import annotations


class Singleton(type):
    __slots__ = ()
    __instances: dict[type, Singleton] = {}

    def __call__(cls) -> Singleton:
        if cls not in cls.__instances:
            cls.__instances[cls] = super(Singleton, cls).__call__()
        return cls.__instances[cls]
