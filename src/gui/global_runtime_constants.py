from __future__ import annotations

from dataclasses import asdict, astuple, dataclass
from tkinter import ttk
from typing import Any, Never, cast


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
    _instance: GlobalRuntimeConstants | None = None
    _can_init: bool = False
    _not_inited_err: str = (
        'instance of GlobalRuntimeConstants not yet initialized, call .configure() once'
    )
    _astuple_cache = None
    _asdict_cache = None

    def __call__(cls, *args, **kwargs) -> GlobalRuntimeConstants | Never:
        if cls._instance is not None:
            return cls._instance
        if not cls._can_init:
            raise RuntimeError(
                'cannot init class by calling it directly, use the .configure() method instead'
            )
        try:
            cls._instance = super().__call__(*args, **kwargs)
            return cls._instance  # type: ignore
        finally:
            cls._can_init = False

    @property
    def configure(cls) -> type[GlobalRuntimeConstants] | Never:
        if cls._instance is not None:
            raise RuntimeError(
                'only allowed instance already initialized, call the class/object to retrieve it'
            )
        cls._can_init = True
        return cls  # type: ignore

    @property
    def __getitem__(cls):
        return cls.__getattribute__

    def astuple(cls) -> tuple[Any, ...] | Never:
        if cls._instance is None:
            raise RuntimeError(cls._not_inited_err)
        if cls.__astuple_cache is None:
            cls.__astuple_cache = astuple(cls._instance)
        return cls.__astuple_cache

    def asdict(cls) -> dict[str, Any] | Never:
        if cls._instance is None:
            raise RuntimeError(cls._not_inited_err)
        if cls.__asdict_cache is None:
            cls.__asdict_cache = asdict(cls._instance)
        return cls.__asdict_cache

    def is_initialized(cls) -> bool:
        """Whether the dataclass (singleton) has been initialized."""
        return cls._instance is not None

    def try_get(cls, attr: str, default: Any = None) -> Any:
        """Returns value of attribute IF AND ONLY IF dataclass has been initialized;
        otherwise, return None.
        """
        if cls._instance is None:
            return default
        try:
            return getattr(cls._instance, attr, default)
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
