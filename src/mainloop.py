from __future__ import annotations

from src import bootstrap
from src.crawl.steps.step import execute_in_order
from src.gui.app import App
from src.gui.global_runtime_constants import GlobalRuntimeConstants

import asyncio
import functools
import itertools

from pathlib import Path

from playwright.async_api import async_playwright


TASK_LIMIT = 5

task_counter = itertools.count(1)

default_step_order: tuple[str, ...] = tuple()

app_dir = bootstrap.Directory()


def get_firefox_exe() -> Path | None:
    path: Path | None = None
    try:
        gen = app_dir.PLAYWRIGHT.glob('firefox-*/firefox/firefox.exe')
        path = next(gen)
        gen.close()
    except (GeneratorExit, StopIteration):
        pass
    return path


async def mainloop():
    if not app_dir.is_ensured():
        app_dir.ensure_mkdir()

    async with async_playwright() as p:
        firefox_exe = get_firefox_exe()
        browser = await p.firefox.launch(executable_path=firefox_exe, headless=False)
        context = await browser.new_context()
        task_sem = asyncio.Semaphore(TASK_LIMIT)
        task_queue = asyncio.Queue()
        new_page = functools.partial(context.new_page)

        def task_can_create() -> bool:
            return not (task_queue.empty() or task_sem.locked())

        def release_semaphore(*_) -> None:
            nonlocal task_sem
            task_sem.release()

        app = App()

        GlobalRuntimeConstants.configure(style=ttk.Style(app))

        import src.gui.asyncio as gui_asyncio

        while await asyncio.sleep(app.frametime, True):
            app.tick()
            if app.has_quit():
                break
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
