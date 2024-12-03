from __future__ import annotations

import os
import asyncio
import hashlib
import tkinter as tk

from asyncio import Future
from concurrent.futures import ProcessPoolExecutor
from contextvars import Context, ContextVar
from tkinter import ttk
from typing import Any, Callable, TypeVar


_workers: int = 2
if (count := os.cpu_count()) is not None and count < _workers:
    _workers = count

executor = ProcessPoolExecutor(_workers)

T = TypeVar('T')

_tkinter_task_counter: int = 0
_tkinter_should_block_var = False


def tkinter_exchedule_and_block(
    widget: ttk.Widget,
    func: Callable[[], T],
    on_done: Callable[[T], None] | None = None,
) -> None:
    global _tkinter_task_counter, _tkinter_should_block_var

    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(executor, func)

    task_id: str = str(_tkinter_task_counter).ljust(3, '0')
    task_hash: str = (
        hashlib.md5(task_id.encode(), usedforsecurity=False).hexdigest().upper()
    )
    event_name = f'<<__TkinterBlockingTask-{task_id}-{task_hash}__>>'

    def event_callback(_: tk.Event):
        import contextvars

        context = {var.name: var.get() for var in contextvars.copy_context().keys()}

        future: Future = context['future']
        widget: ttk.Widget = context['widget']
        event_name: str = context['event_name']
        on_done: Callable | None = context['on_done']

        try:
            result = future.result()
        except Exception as err:
            raise err  # just to be clear it may raise
        if on_done is not None:
            on_done(result)
        widget.unbind(event_name)

    def register_tk_event(_: asyncio.Future):
        global _tkinter_should_block_var

        import contextvars

        context = {var.name: var.get() for var in contextvars.copy_context().keys()}

        widget: ttk.Widget = context['widget']
        event_name: str = context['event_name']
        event_callback: Callable[[tk.Event], None] = context['event_callback']

        widget.bind(event_name, event_callback)
        widget.event_generate(event_name)
        _tkinter_should_block_var = False

    # new context to ensure references to objects
    ctx = Context()
    ctx_widget = ctx.run(ContextVar, 'widget')
    ctx.run(ctx_widget.set, widget)
    ctx_event_name = ctx.run(ContextVar, 'event_name')
    ctx.run(ctx_event_name.set, event_name)
    ctx_on_done = ctx.run(ContextVar, 'on_done')
    ctx.run(ctx_on_done.set, on_done)
    ctx_future = ctx.run(ContextVar, 'future')
    ctx.run(ctx_future.set, future)
    ctx_event_callback = ctx.run(ContextVar, 'event_callback')
    ctx.run(ctx_event_callback.set, event_callback)

    _tkinter_should_block_var = True

    future.add_done_callback(register_tk_event, context=ctx)

    _tkinter_task_counter += 1


def tkinter_should_block() -> bool:
    return _tkinter_should_block_var
