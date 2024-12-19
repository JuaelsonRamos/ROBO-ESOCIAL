from __future__ import annotations

from src import bootstrap
from src.crawl.steps.step import execute_in_order
from src.db import init_sync_sqlite
from src.gui.app import App
from src.gui.tkinter_global import TkinterGlobal

import sys
import asyncio
import argparse

from pathlib import Path
from tkinter import ttk
from types import NoneType
from typing import Final

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)


TASK_LIMIT = 5


app_dir = bootstrap.Directory()


def parse_cli_args():
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        prog='ROBO-ESOCIAL',
        argument_default=None,
        exit_on_error=False,
        add_help=True,
    )
    parser.add_argument('--no-playwright', action='store_true')
    parser.add_argument('--no-tkinter', action='store_true')
    args = parser.parse_args(sys.argv[1:] if __debug__ else [])
    if args.no_playwright and args.no_tkinter:
        raise RuntimeError(
            'cannot specify both arguments --no-tkinter and --no-playwright'
        )
    return args


CLI_ARGS: Final[argparse.Namespace] = parse_cli_args()


class BrowserRuntime:
    default_step_order: tuple[str, ...] = ()

    def __init__(self, p: Playwright) -> None:
        super().__init__()
        self.p = p
        self.firefox_exe = self.get_firefox_exe()
        self._browser = None
        self._context = None
        self.semaphore = asyncio.Semaphore(TASK_LIMIT)
        self.queue = asyncio.Queue()
        self.task_i: int = 1

    @classmethod
    def should_avoid(cls) -> bool:
        global CLI_ARGS
        return getattr(CLI_ARGS, 'no_playwright', False)

    @classmethod
    async def single_isolated_runtime_loop(cls) -> None:
        async with async_playwright() as p:
            instance = cls(p)
            while True:
                await instance.create_task(raise_if_cant=False)

    def can_create_task(self) -> bool:
        return not (self.queue.empty() or self.semaphore.locked())

    def _on_task_done(self, _: asyncio.Task[None]) -> None:
        self.semaphore.release()

    def get_firefox_exe(self) -> Path | None:
        path: Path | None = None
        try:
            gen = app_dir.PLAYWRIGHT.glob('firefox-*/firefox/firefox.exe')
            path = next(gen)
            gen.close()
        except (GeneratorExit, StopIteration):
            pass
        return path

    async def create_task(self, *, raise_if_cant: bool) -> asyncio.Task[None] | None:
        if self.queue.empty() or self.semaphore.locked():
            # can't create task, awaiting semaphore would halt coroutine indefinitely
            if not raise_if_cant:
                # consumer doesn't want it to raise on error
                return
            raise self.CannotCreateTaskError(
                'either queue is empty or semaphore is closed'
            )
        await self.semaphore.acquire()
        index_string = str(self.task_i).ljust(3, '0')
        name = f'crawler({index_string})'
        browser = self._browser or await self.browser()
        context = self._context or await self.context()
        page = await self.new_page()
        coro = execute_in_order(browser, context, page, self.default_step_order)
        task = asyncio.create_task(coro, name=name)
        task.add_done_callback(self._on_task_done)
        self.task_i += 1
        return task

    async def browser(self) -> Browser:
        if self._browser is None:
            self._browser = await self.p.firefox.launch(
                executable_path=self.firefox_exe, headless=False
            )
        return self._browser

    async def context(self) -> BrowserContext:
        browser = self._browser or await self.browser()
        if self._context is None:
            self._context = await browser.new_context()
        return self._context

    async def new_page(self) -> Page:
        context = self._context or await self.context()
        return await context.new_page()


class GraphicalRuntime:
    def __init__(self) -> NoneType:
        super().__init__()
        self.app = App()

        TkinterGlobal.style = ttk.Style(self.app)

        import src.gui.asyncio as gui_asyncio

        self.gui_asyncio_helpers = gui_asyncio

    def stop_all_threads(self):
        self.gui_asyncio_helpers.Thread.stop_all()

    @classmethod
    def should_avoid(cls) -> bool:
        global CLI_ARGS
        return getattr(CLI_ARGS, 'no_tkinter', False)

    @classmethod
    def single_isolated_runtime_loop(cls) -> None:
        instance = cls()
        instance.app.mainloop()


async def production_runtime_loop(browser: BrowserRuntime, gui: GraphicalRuntime):
    try:
        while await asyncio.sleep(gui.app.frametime, True):
            gui.app.tick()
            if gui.app.has_quit():
                break
            while browser.can_create_task():
                await browser.create_task(raise_if_cant=True)
    finally:
        gui.stop_all_threads()


async def mainloop():
    if not app_dir.is_ensured():
        app_dir.ensure_mkdir()

    if BrowserRuntime.should_avoid():
        init_sync_sqlite()
        GraphicalRuntime.single_isolated_runtime_loop()
        return
    if GraphicalRuntime.should_avoid():
        init_sync_sqlite()
        await BrowserRuntime.single_isolated_runtime_loop()
        return

    init_sync_sqlite()
    async with async_playwright() as p:
        browser_runtime = BrowserRuntime(p)
        graphical_runtime = GraphicalRuntime()
        await production_runtime_loop(browser_runtime, graphical_runtime)
