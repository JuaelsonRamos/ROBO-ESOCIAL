from __future__ import annotations

from src.bootstrap import bootstrap_application
from src.global_state import init_global_state
from src.gui.app import GraphicalRuntime
from src.sistema.crawl import BrowserRuntime

import asyncio

from playwright.async_api import async_playwright


async def mainloop():
    bootstrap_application()
    async with async_playwright() as p:
        browser = BrowserRuntime(p)
        gui = GraphicalRuntime()
        init_global_state(gui, browser)
        while await asyncio.sleep(gui.app.frametime, True):
            gui.app.tick()
            if gui.app.has_quit():
                break
            if browser.can_schedule_task():
                await browser.schedule_task()
