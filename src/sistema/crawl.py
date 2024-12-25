from __future__ import annotations

from src.bootstrap import Directory
from src.db.tables import BrowserContextDict, CookieDict, LocalStorageDict, OriginDict
from src.exc import Task
from src.runtime import CommandLineArguments
from src.types import BrowserType

import asyncio
import hashlib
import inspect
import itertools

from asyncio import Queue, Semaphore
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Coroutine, Final
from urllib.parse import (
    ParseResult as URLParseResult,
    urlparse,
)

import playwright.async_api as playwright


ESOCIAL_URL: Final[URLParseResult]  # TODO
GOVBR_URL: Final[URLParseResult]  # TODO


def default_browsercontext_dict() -> BrowserContextDict: ...


def make_db_browsercontext_dict() -> BrowserContextDict: ...


def make_db_origin_dict() -> OriginDict: ...


def make_db_cookie_dict() -> CookieDict: ...


def make_db_local_storage_dict() -> LocalStorageDict: ...


def browserhook_on_cookie_change() -> None: ...


def browserhook_on_local_storage_change() -> None: ...


@dataclass(init=True, slots=True)
class PageState:
    origin_id: int | None
    cookie_ids: set[int]
    local_storage_ids: set[int]
    page_init_url: URLParseResult
    page: playwright.Page

    def state_hash(self) -> int:
        return (
            hash(self.origin_id) + hash(self.cookie_ids) + hash(self.local_storage_ids)
        )


class BrowserContext:
    def __init__(self, p: playwright.Playwright, browser: playwright.Browser) -> None:
        self.p = p
        self.browser = browser
        self.browser_exe = Path(browser.browser_type.executable_path)
        self.browser_type = BrowserType.enum_from_name(browser.browser_type.name)

    def create_new(self):
        self.browsercontext_id: int
        self.browser_context: playwright.BrowserContext

    def create_from(self, *args):
        self.browsercontext_id: int
        self.browser_context: playwright.BrowserContext

    @staticmethod
    def firefox_exe() -> Path | None:
        path: Path | None = None
        try:
            gen = Directory.PLAYWRIGHT.glob('firefox-*/firefox/firefox.exe')
            path = next(gen)
            gen.close()
        except (GeneratorExit, StopIteration):
            pass
        return path

    async def new_page(self) -> PageState:
        parsed_url = urlparse()  # TODO
        page = await self.browser_context.new_page()
        return PageState(0, set(), set(), parsed_url, page)


StepFunc = Callable[['CrawlerTask'], None]


class CrawlerTask:
    _get_task_i = itertools.count(0).__next__
    tasks: dict[str, CrawlerTask] = {}
    _steps: tuple[StepFunc, ...]

    def __init__(
        self, p: playwright.Playwright, context: BrowserContext, runtime: BrowserRuntime
    ) -> None:
        self.p = p
        self.context = context
        self.runtime = runtime

    async def _crawler_run(self):
        for step in self._steps:
            if inspect.iscoroutinefunction(step):
                await step(self)
                continue
            if inspect.isfunction(step):
                step(self)

    async def start(self, *, return_if_cant: bool = False) -> None:
        if return_if_cant and not self.runtime.can_create_task():
            return
        await self.runtime.semaphore.acquire()
        self.task_index: int = self._get_task_i()
        self.task_index_formated: str = str(self.task_index).ljust(3, '0')
        self.task_name: str = f'crawler({self.task_index_formated})'
        self.page: PageState = await self.context.new_page()
        self.asyncio_coro: Coroutine = self._crawler_run()
        self.asyncio_task: asyncio.Task = asyncio.create_task(
            self.asyncio_coro, name=self.task_name
        )
        self.asyncio_task.add_done_callback(self._asyncio_task_done_hook)
        self.runtime.lifetime_task_count += 1

    def _asyncio_task_done_hook(self, task: asyncio.Task[None]) -> None:
        self.runtime.semaphore.release()
        self.unregister_self()

    def register_self(self):
        self.task_id: str = hashlib.md5(hash(self).to_bytes()).hexdigest().upper()
        self.tasks[self.task_id] = self

    def unregister_self(self):
        if hasattr(self, 'task_id') and self.task_id in self.tasks:
            del self.tasks[self.task_id]

    def __hash__(self) -> int:
        non_unique = hash(self.context.browser_exe) + hash(
            self.context.browser_type.playwright_name()
        )
        unique = hash(self.task_index)
        return non_unique + unique

    @classmethod
    def define_steps_in_order(cls, *steps: StepFunc) -> None:
        if hasattr(cls, '_steps'):
            return
        if any(not hasattr(func, '__crawler_step__') for func in steps):
            raise Task.CannotRegisterStep(
                'function to register was not defined as a CrawlerTask.step'
            )
        cls._steps = tuple(steps)

    @classmethod
    def step(cls, func: StepFunc) -> StepFunc:
        func.__crawler_step__ = True
        return func


class BrowserRuntime:
    cli_args = CommandLineArguments().parse_argv()
    SEMAPHORE_LIMIT: Final[int] = 5
    sheet_queue: Queue[Path] = Queue()
    browser: playwright.Browser

    def __init__(self, p: playwright.Playwright) -> None:
        self.p = p
        self.semaphore: Semaphore = Semaphore(self.SEMAPHORE_LIMIT)
        self.lifetime_task_count: int = 0

    @classmethod
    def should_run(cls) -> bool:
        return not cls.cli_args.no_playwright

    def can_create_task(self) -> bool:
        return not (self.sheet_queue.empty() or self.semaphore.locked())


CrawlerTask.define_steps_in_order  # TODO
