from __future__ import annotations

from src.utils import Singleton

import asyncio

from asyncio import Future
from concurrent.futures import ProcessPoolExecutor
from tkinter import ttk
from typing import Any, Callable, Generic, TypeVar


RetValue = TypeVar('RetValue', Any, Exception)


class TkinterLock(Generic[RetValue], metaclass=Singleton):
    def __init__(self) -> None:
        self.executor = ProcessPoolExecutor(1)
        self.loop = asyncio.get_event_loop()
        self._lock: bool = False
        self._state = {}

    def locked(self) -> bool:
        return self._lock

    def is_future_running(self) -> bool:
        fut: Future = self._state.get('future', None)
        return fut is not None and (fut.done() or fut.cancelled())

    def get_running_future(self) -> Future | None:
        return self._state.get('future', None)

    def get_scheduler_widget(self) -> ttk.Widget | None:
        return self._state.get('widget', None)

    def _done_callback(self, fut: Future):
        on_done = self._state.get('on_done', None)
        try:
            if on_done is None:
                return
            result = fut.result()
            on_done(result, False)
        except Exception as err:
            on_done(err, True)
        finally:
            self._lock = False
            self._state.clear()

    def schedule(
        self,
        widget: ttk.Widget,
        func: Callable[[], RetValue],
        on_done: Callable[[RetValue, bool], None] | None = None,
    ) -> None:
        self._lock = True
        fut = self.loop.run_in_executor(self.executor, func)
        self._state.update(widget=widget, callback=func, future=fut)
        if on_done is not None:
            self._state['on_done'] = on_done
            fut.add_done_callback(self._done_callback)
