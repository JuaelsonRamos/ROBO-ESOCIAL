from __future__ import annotations


__all__ = ['register', 'stop_all']

from threading import Event, Thread
from typing import NamedTuple


class ThreadEntry(NamedTuple):
    thread: Thread
    stop_event: Event


_threads: list[ThreadEntry] = []


def register(*, thread: Thread, stop_event: Event):
    _threads.append(ThreadEntry(thread=thread, stop_event=stop_event))


def stop_all():
    for entry in _threads:
        entry.stop_event.set()
        entry.thread.join()
