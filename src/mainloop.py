from __future__ import annotations

from src.bootstrap import Directory
from src.db import init_sync_sqlite
from src.gui.app import App
from src.gui.tkinter_global import TkinterGlobal
from src.runtime import CommandLineArguments
from src.sistema.crawl import BrowserRuntime

import asyncio

from tkinter import ttk
from types import NoneType

from playwright.async_api import async_playwright


class GraphicalRuntime:
    cli_args = CommandLineArguments().parse_argv()

    def __init__(self) -> NoneType:
        super().__init__()
        self.app = App()

    @classmethod
    def should_avoid(cls) -> bool:
        return cls.cli_args.no_tkinter

    @classmethod
    def single_isolated_runtime_loop(cls) -> None:
        instance = cls()
        instance.app.mainloop()


async def mainloop():
    if not Directory.is_ensured():
        Directory.ensure_mkdir()
    sqlite_engine = init_sync_sqlite()
    TkinterGlobal.sqlite = sqlite_engine
    async with async_playwright() as p:
        browser = BrowserRuntime(p)
        TkinterGlobal.sheet_queue = browser.sheet_queue
        gui = GraphicalRuntime()
        TkinterGlobal.style = ttk.Style(gui.app)
        while await asyncio.sleep(gui.app.frametime, True):
            gui.app.tick()
            if gui.app.has_quit():
                break
            if browser.can_schedule_task():
                await browser.schedule_task()
