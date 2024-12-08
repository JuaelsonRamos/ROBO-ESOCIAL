from __future__ import annotations

from dataclasses import asdict, astuple, dataclass
from tkinter import ttk
from typing import Any, Never


class _InitializableSingletonMeta(type):
    """
    Allows dataclass' __init__ to be called once by calling the .configure() method only
    once, then call the class/object to retrieve the same instance.

    The following actions will raise :ref:`RuntimeError`:

    * Calling the class/object before .configure() will raise RuntimeError.
    * Calling .configure() more than once will raise RuntimeError.
    * Calling custom methods (a.k.a doesn't exist in the base dataclass object)
        before calling .configure() may raise RuntimeError.

    Please check for methods returning :ref:`Never`, as they are the ones that may raise.
    """

    __slots__ = ()
    __instance: GlobalRuntimeConstants | None = None
    __can_init: bool = False
    __not_inited_err: str = (
        'instance of GlobalRuntimeConstants not yet initialized, call .configure() once'
    )
    __astuple_cache = None
    __asdict_cache = None

    def __call__(cls, *args, **kwargs) -> GlobalRuntimeConstants | Never:
        if cls.__instance is not None:
            return cls.__instance
        if not cls.__can_init:
            raise RuntimeError(
                'cannot init class by calling it directly, use the .configure() method instead'
            )
        cls.__instance = super().__call__(*args, **kwargs)
        return cls.__instance  # type: ignore

    @property
    def configure(cls) -> GlobalRuntimeConstants | Never:
        if cls.__instance is not None:
            raise RuntimeError(
                'only allowed instance already initialized, call the class/object to retrieve it'
            )
        try:
            cls.__can_init = True
            return cls  # type: ignore
        finally:
            cls.__can_init = False

    @property
    def __getitem__(cls):
        return cls.__getattribute__

    def __getattribute__(cls, name: str) -> Any | Never:
        if cls.__instance is None:
            raise RuntimeError(cls.__not_inited_err)
        return super().__getattribute__(name)  # type: ignore

    def astuple(cls) -> tuple[Any, ...] | Never:
        if cls.__instance is None:
            raise RuntimeError(cls.__not_inited_err)
        if cls.__astuple_cache is None:
            cls.__astuple_cache = astuple(cls.__instance)
        return cls.__astuple_cache

    def asdict(cls) -> dict[str, Any] | Never:
        if cls.__instance is None:
            raise RuntimeError(cls.__not_inited_err)
        if cls.__asdict_cache is None:
            cls.__asdict_cache = asdict(cls.__instance)
        return cls.__asdict_cache

    def is_initialized(cls) -> bool:
        """Whether the dataclass (singleton) has been initialized."""
        return cls.__instance is not None

    def try_get(cls, attr: str, default: Any = None) -> Any:
        """Returns value of attribute IF AND ONLY IF dataclass has been initialized;
        otherwise, return None.
        """
        if cls.__instance is None:
            return default
        try:
            return getattr(cls.__instance, attr, default)
        except RuntimeError:
            return default


class _InitializableSingleton(_InitializableSingletonMeta):
    """Dummy class to prevent metaclass' __call__ method from confusing the static type
    checker.
    """


@dataclass(frozen=True, slots=True, kw_only=True)
class GlobalRuntimeConstants(metaclass=_InitializableSingleton):
    """
    Dataclass holding constant references to values expected to be used throught the
    application as global values.

    All values must be initialized, and to avoid bugs, preferably before any user action
    is performed.
    """

    style: ttk.Style
