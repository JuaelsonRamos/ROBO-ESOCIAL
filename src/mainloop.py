from __future__ import annotations

from src.crawl.steps.step import execute_in_order
from src.gui.app import App
from src.gui.lock import TkinterLock
from src.windows import get_monitor_settings

import math
import asyncio
import functools
import itertools

from playwright.async_api import async_playwright


TASK_LIMIT = 5

task_counter = itertools.count(1)

default_step_order: tuple[str, ...] = tuple()


async def mainloop():
    monitors_fps: list[int | float] = [
        monitor.DisplaySettings.DisplayFrequency for monitor in get_monitor_settings()
    ]
    best_device_fps: int = math.ceil(max(monitors_fps))
    app_fps: int = best_device_fps if 15 <= best_device_fps <= 75 else 60
    app_tick: float = 1 / app_fps  # miliseconds

    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context()
        task_sem = asyncio.Semaphore(TASK_LIMIT)
        task_queue = asyncio.Queue()
        new_page = functools.partial(context.new_page)
        gui_lock = TkinterLock()

        def task_can_create() -> bool:
            return not (task_queue.empty() or task_sem.locked())

        def release_semaphore(*_) -> None:
            nonlocal task_sem
            task_sem.release()

        tk_root = App()

        import src.gui.styles as gui_style
        import src.gui.asyncio as gui_asyncio

        gui_style.default()

        while await asyncio.sleep(app_tick, True):
            if not gui_lock.locked():
                tk_root.update_idletasks()
                tk_root.update()
            while task_can_create():
                await task_sem.acquire()
                task_i = str(next(task_counter)).ljust(3, '0')
                task_name = f'crawler({task_i})'
                task_coro = execute_in_order(
                    browser, context, await new_page(), default_step_order
                )
                task = asyncio.create_task(task_coro, name=task_name)
                task.add_done_callback(release_semaphore)

        gui_asyncio.Thread.stop_all()
