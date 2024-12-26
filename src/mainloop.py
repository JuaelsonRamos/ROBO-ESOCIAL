from __future__ import annotations

from src.bootstrap import Directory
from src.db import init_sync_sqlite
from src.gui.app import App
from src.gui.tkinter_global import TkinterGlobal
from src.sistema.crawl import BrowserRuntime

import sys
import asyncio
import argparse

from tkinter import ttk
from types import NoneType
from typing import Final

from playwright.async_api import async_playwright


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


class GraphicalRuntime:
    def __init__(self) -> NoneType:
        super().__init__()
        self.app = App()

        TkinterGlobal.style = ttk.Style(self.app)

    @classmethod
    def should_avoid(cls) -> bool:
        global CLI_ARGS
        return getattr(CLI_ARGS, 'no_tkinter', False)

    @classmethod
    def single_isolated_runtime_loop(cls) -> None:
        instance = cls()
        instance.app.mainloop()


async def mainloop():
    if not Directory.is_ensured():
        Directory.ensure_mkdir()
    init_sync_sqlite()
    async with async_playwright() as p:
        browser = BrowserRuntime(p)
        gui = GraphicalRuntime()
        while await asyncio.sleep(gui.app.frametime, True):
            gui.app.tick()
            if gui.app.has_quit():
                break
            if browser.can_schedule_task():
                await browser.schedule_task()
