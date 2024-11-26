from __future__ import annotations

from typing import Any, Callable, Sequence


__all__ = ['Thread']

import time
import threading as t

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ThreadEvents:
    start: t.Event = field(default_factory=t.Event)
    stop: t.Event = field(default_factory=t.Event)


class Thread(t.Thread):
    _all_threads: list[Thread] = []

    @classmethod
    def stop_all(cls):
        sorted_by_delay = sorted(cls._all_threads, key=lambda th: th.attempt_delay)
        for thread in sorted_by_delay:
            try:
                thread.events.stop.set()
                thread.join()
            except Exception:
                continue

    def __init__(
        self,
        target: Callable[[], None] = None,
        name: str = None,
        args: Sequence[Any] = (),
        kwargs: dict[str, Any] = None,
        *,
        attempt_delay: float,
    ):
        super().__init__(
            target=self.runtime_factory(target),
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=None,
        )
        self.attempt_delay = attempt_delay
        self.events = ThreadEvents()
        self._all_threads.append(self)

    def runtime_factory(self, callback):
        if not callable(callback):
            raise ValueError('callback value is not callable')

        def runtime():
            while True:
                if self.events.stop.is_set():
                    self.events.stop.clear()
                    break
                if self.events.start.is_set():
                    callback()
                    self.events.start.clear()
                time.sleep(self.attempt_delay)

        return runtime
