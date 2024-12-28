from __future__ import annotations

from .browser_config import FirefoxConfig

from src.bootstrap import Directory
from src.db.tables import (
    BrowserContext as _BrowserContext,
    BrowserContextDict,
    BrowserType,
    ClientCertificate as _ClientCertificate,
    ColorSchemeType,
    CookieDict,
    EntryWorksheet as _EntryWorksheet,
    EntryWorksheetDict,
    ForcedColorsType,
    LocalStorageDict,
    LocaleType,
    OriginDict,
    ProcessingEntry as _ProcessingEntry,
    ProcessingEntryDict,
    ReducedMotionType,
    TimezoneIdType,
    Worksheet as _Worksheet,
)
from src.exc import Task
from src.runtime import CommandLineArguments
from src.sistema.sheet import SheetValidator
from src.types import TaskInitState

import asyncio
import hashlib
import inspect
import itertools

from asyncio import Lock, Queue, Semaphore
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine, Final, TypedDict, cast
from urllib.parse import (
    ParseResult as URLParseResult,
    urlparse,
)

import playwright.async_api as playwright

from sqlalchemy import func


ESOCIAL_URL: Final[URLParseResult]  # TODO
GOVBR_URL: Final[URLParseResult]  # TODO


def make_db_origin_dict() -> OriginDict: ...


def make_db_cookie_dict() -> CookieDict: ...


def make_db_local_storage_dict() -> LocalStorageDict: ...


class CookieChangeDetail(TypedDict):
    oldCookie: str
    newCookie: str


def browserhook_on_cookie_change(detail: CookieChangeDetail) -> None:
    pass


class LocalStorageState(TypedDict):
    length: int
    keys: list[str]
    storageContent: dict[str, Any]


class LocalStorageDetail(TypedDict):
    oldLocalStorage: str  # strigfied LocalStorageState
    newLocalStorage: str  # strigfied LocalStorageState


def browserhook_on_local_storage_change(detail: LocalStorageDetail) -> None:
    pass


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
    # db properties
    accept_downloads: bool
    offline: bool
    javascript_enabled: bool
    is_mobile: bool
    has_touch: bool
    colorscheme: ColorSchemeType
    reduced_motion: ReducedMotionType
    forced_colors: ForcedColorsType
    locale: LocaleType
    timezone_id: TimezoneIdType

    def __init__(self, p: playwright.Playwright, browser: playwright.Browser) -> None:
        self.p = p
        self.browser = browser
        self.browser_exe = Path(browser.browser_type.executable_path)
        self.browser_type: BrowserType = cast(BrowserType, browser.browser_type.name)
        self._db_data_cache: dict[str, Any] = {}
        self._db_data_changes: dict[str, Any] = {}

    @staticmethod
    def default_db_dict() -> BrowserContextDict:
        return {
            'accept_downloads': False,
            'offline': False,
            'javascript_enabled': True,
            'is_mobile': False,
            'has_touch': False,
            'colorscheme': 'light',
            'reduced_motion': 'reduce',
            'forced_colors': 'none',
            'locale': 'pt-BR',
            'timezone_id': 'America/Sao_Paulo',
        }

    def _create_db_data_populate_self(self, init_state: TaskInitState):
        # caching init data
        self.workbook_id = init_state['workbook_db_id']
        self.certificate_db_id = init_state['certificate_db_id']
        self.worksheet_ids = _Worksheet.get_sheet_ids_from_book_id(self.workbook_id)

        # insert browser context data into db
        db_data = self.default_db_dict()
        self.browsercontext_id: int = _BrowserContext.sync_insert_one(db_data)

        # save data as in db
        inserted_db_data = _BrowserContext.sync_select_one_from_id(
            self.browsercontext_id
        )
        if inserted_db_data is None:
            raise RuntimeError('data not inserted')
        data = inserted_db_data._asdict()
        self._db_data_cache = data
        self.created: datetime = data['created']
        self.last_modified: datetime | None = data['last_modified']
        self.accept_downloads: bool = data['accept_downloads']
        self.offline: bool = data['offline']
        self.javascript_enabled: bool = data['javascript_enabled']
        self.is_mobile: bool = data['is_mobile']
        self.has_touch: bool = data['has_touch']
        self.colorscheme: ColorSchemeType = data['colorscheme']
        self.reduced_motion: ReducedMotionType = data['reduced_motion']
        self.forced_colors: ForcedColorsType = data['forced_colors']
        self.locale: LocaleType = data['locale']
        self.timezone_id: TimezoneIdType = data['timezone_id']

    def _make_playwright_context_args(self) -> dict[str, Any]:
        indb = self._db_data_cache
        cert = _ClientCertificate.sync_select_one_from_id(self.certificate_db_id)
        cert_dict = None
        if cert is not None:
            cert_dict = {'origin': cert.origin}
            if cert.using_type == 'PFX':
                cert_dict['pfx'] = cert.pfx if cert.pfx is not None else b''
            elif cert.usign_type == 'KEY':
                cert_dict['key'] = cert.key if cert.key is not None else b''
            else:
                cert_dict['cert'] = cert.cert if cert.cert is not None else b''
            if cert.passphrase is not None:
                cert_dict['passphrase'] = cert.passphrase
        return dict(
            java_script_enabled=indb['javascript_enabled'],
            locale=indb['locale'],
            timezone_id=indb['timezone_id'],
            offline=indb['offline'],
            is_mobile=indb['is_mobile'],
            has_touch=indb['has_touch'],
            color_scheme=indb['colorscheme'],
            reduced_motion=indb['reduced_motion'],
            forced_colors=indb['forced_colors'],
            accept_downloads=indb['accept_downloads'],
            client_certificates=[cert_dict] if cert_dict is not None else None,
        )

    async def start_from(self, init_state: TaskInitState):
        self._create_db_data_populate_self(init_state)
        args = self._make_playwright_context_args()
        self.browser_context: playwright.BrowserContext = (
            await self.browser.new_context(**args)
        )

        # expose functions first
        await self.browser_context.expose_function(
            '_localStorageChangeHandler', browserhook_on_local_storage_change
        )
        await self.browser_context.expose_function(
            '_cookieChangeHandler', browserhook_on_cookie_change
        )

        # add scripts after exposing functions
        await self.browser_context.add_init_script(
            path=Path('./js/meta/cookieChange.js')
        )
        await self.browser_context.add_init_script(
            path=Path('./js/meta/localStorageChange.js')
        )

    def __setattr__(self, name: str, value: Any, /) -> None:
        if name in self._db_data_cache:
            self._db_data_changes[name] = value
            return
        setattr(super(), name, value)

    def can_update_db_data(self) -> bool:
        return len(self._db_data_changes) > 0

    def update_db_data(self):
        if (
            len(self._db_data_changes) == 0
            or len(self._db_data_cache) == 0
            or '_id' not in self._db_data_cache
        ):
            return
        _BrowserContext.sync_update_one_from_id(
            self._db_data_changes, self._db_data_cache['_id']
        )
        self._db_data_changes.clear()

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


class ProcessingEntryManager:
    def __init__(
        self, browser_context_id: int, workbook_id: int, client_certificate_id: int
    ) -> None:
        self.browser_context_id: int = browser_context_id
        self.workbook_id: int = workbook_id
        self.client_certificate_id: int = client_certificate_id

    def init_db_data(self) -> None:
        initial_data = self._initial_db_data()
        self.db_id = _ProcessingEntry.sync_insert_one(initial_data)
        self._update_current_db_data()

    def _update_current_db_data(self) -> None:
        db_data = _EntryWorksheet.sync_select_one_from_id(self.db_id)
        self.current_db_data: dict[str, int | datetime | bool]
        data = db_data._asdict()  # type: ignore
        self.current_db_data = data
        self.created: datetime = data['created']
        self.last_modified: datetime | None = data['last_modified']
        self.has_started: bool = data['has_started']
        self.is_paused: bool = data['is_paused']
        self.has_finished: bool = data['has_finished']
        self.when_started: datetime | None = data['when_started']
        self.when_last_started: datetime | None = data['when_last_started']
        self.when_finished: datetime | None = data['when_finished']
        self.when_last_paused: datetime | None = data['when_last_paused']

    def _initial_db_data(self) -> ProcessingEntryDict:
        return {
            'has_started': False,
            'is_paused': False,
            'has_finished': False,
            'when_started': None,
            'when_last_started': None,
            'when_finished': None,
            'when_last_paused': None,
            'browsercontext_id': self.browser_context_id,
            'workbook_id': self.workbook_id,
            'clientcertificate_id': self.client_certificate_id,
        }

    def set_started(self) -> None:
        data = {
            'has_started': True,
            'when_started': func.now(),
            'when_last_started': func.now(),
        }
        _ProcessingEntry.sync_update_one_from_id(data, self.db_id)
        self._update_current_db_data()

    def set_finished(self) -> None:
        data = {'has_finished': True, 'when_finished': func.now()}
        _ProcessingEntry.sync_update_one_from_id(data, self.db_id)
        self._update_current_db_data()

    def set_paused(self) -> None:
        data = {'is_paused': True, 'when_last_paused': func.now()}
        _ProcessingEntry.sync_update_one_from_id(data, self.db_id)
        self._update_current_db_data()

    def unset_paused(self) -> None:
        data = {'is_paused': False, 'when_last_started': func.now()}
        _ProcessingEntry.sync_update_one_from_id(data, self.db_id)
        self._update_current_db_data()


class EntryWorksheetManager:
    def __init__(self, processing_entry_id: int, worksheet_id: int):
        self.processing_entry_id: int = processing_entry_id
        self.worksheet_id: int = worksheet_id

    def init_db_data(self) -> None:
        initial_data = self._initial_db_data()
        self.db_id: int = _EntryWorksheet.sync_insert_one(initial_data)
        self._update_current_db_data()

    def _update_current_db_data(self):
        db_data = _EntryWorksheet.sync_select_one_from_id(self.db_id)
        self.current_db_data: dict[str, int]
        data = db_data._asdict()  # type: ignore
        self.current_db_data = data
        self.created: datetime = data['created']
        self.last_modified: datetime | None = data['last_modified']
        self.processingentry_id: int = data['processingentry_id']
        self.worksheet_id: int = data['worksheet_id']
        self.last_column: int = data['last_column']
        self.last_row: int = data['last_row']

    def _initial_db_data(self) -> EntryWorksheetDict:
        return {
            'processingentry_id': self.processing_entry_id,
            'worksheet_id': self.worksheet_id,
            'last_column': 0,
            'last_row': 0,
        }

    def bump_last_column(self) -> None:
        data = {'last_column': self.last_column + 1}
        _EntryWorksheet.sync_update_one_from_id(data, self.db_id)

    def bump_last_row(self) -> None:
        data = {'last_row': self.last_row + 1}
        _EntryWorksheet.sync_update_one_from_id(data, self.db_id)


class CrawlerTask:
    _get_task_i = itertools.count(0).__next__
    tasks: dict[str, CrawlerTask] = {}
    _steps: tuple[StepFunc, ...]
    sheet_validator: SheetValidator

    def __init__(
        self, p: playwright.Playwright, context: BrowserContext, runtime: BrowserRuntime
    ) -> None:
        self.p = p
        self.context = context
        self.runtime = runtime

    async def _crawler_run(self):
        await self.runtime.semaphore.acquire()
        await self.runtime.task_count_increase()
        self.processing_entry_manager = ProcessingEntryManager(
            self.context.browsercontext_id,
            self.context.workbook_id,
            self.context.certificate_db_id,
        )
        self.processing_entry_manager.init_db_data()
        if len(self.context.worksheet_ids) == 0:
            # create overall processing entry, but exit it without doing anything if
            # anything can be done
            return
        self.worksheet_managers: list[EntryWorksheetManager] = []
        self.page: PageState = await self.context.new_page()
        for worksheet_id in self.context.worksheet_ids:
            self.current_entry_worksheet_manager = EntryWorksheetManager(
                self.processing_entry_manager.db_id, worksheet_id
            )
            self.worksheet_managers.append(self.current_entry_worksheet_manager)
            self.current_entry_worksheet_manager.init_db_data()
            for step in self._steps:
                if self.context.can_update_db_data():
                    self.context.update_db_data()
                if not getattr(step, '__crawler_step__', False):
                    continue
                if inspect.iscoroutinefunction(step):
                    await step(self)
                    continue
                if inspect.isfunction(step):
                    step(self)

    def schedule_self(self, *, return_if_cant: bool = False) -> None:
        if return_if_cant and not self.runtime.can_task_run_immediately():
            return
        self.task_index: int = self._get_task_i()
        self.task_index_formated: str = str(self.task_index).ljust(3, '0')
        self.task_name: str = f'crawler({self.task_index_formated})'
        self.asyncio_coro: Coroutine = self._crawler_run()
        self.asyncio_task: asyncio.Task = asyncio.create_task(
            self.asyncio_coro, name=self.task_name
        )
        self.asyncio_task.add_done_callback(self._asyncio_task_done_hook)

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
    def define_steps_in_strict_order(cls, *steps: StepFunc) -> None:
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
    SPREADSHEET_QUEUE_LIMIT: Final[int] = 0  # 0 == 'unlimited'
    browser: playwright.Browser

    def __init__(self, p: playwright.Playwright) -> None:
        self.p = p
        self.semaphore: Semaphore = Semaphore(self.SEMAPHORE_LIMIT)
        self.sheet_queue: Queue[TaskInitState] = Queue(self.SPREADSHEET_QUEUE_LIMIT)
        self._lifetime_task_count: int = 0
        self._task_count_lock = Lock()

    @property
    def lifetime_task_count(self) -> int:
        return self._lifetime_task_count

    async def task_count_increase(self):
        async with self._task_count_lock:
            self._lifetime_task_count += 1

    @classmethod
    def should_run(cls) -> bool:
        return not cls.cli_args.no_playwright

    def can_task_run_immediately(self) -> bool:
        return not (self.sheet_queue.empty() and self.semaphore.locked())

    def can_schedule_task(self) -> bool:
        return not self.sheet_queue.empty()

    async def new_firefox(self) -> playwright.Browser:
        exe = BrowserContext.firefox_exe()
        if exe is None:
            raise RuntimeError('cannot find firefox executable')

        readwrite = 0o666
        readonly = 0o444

        # firefox distribution config dir
        dist_dir = exe.parent / 'distribution'
        if not dist_dir.exists():
            dist_dir.mkdir(parents=True, exist_ok=True)

        # check/write override.ini
        override_path = dist_dir / 'override.ini'
        if not override_path.exists():
            override_path.touch(readwrite, exist_ok=True)
        file_hash = FirefoxConfig.hash_override_ini(ini_file=override_path)
        dict_hash = FirefoxConfig.hash_override_ini()
        if file_hash != dict_hash:
            if override_path.stat().st_mode != readwrite:
                override_path.chmod(readwrite)
            override_path.write_bytes(FirefoxConfig.parse_override_ini())
        if override_path.stat().st_mode != readonly:
            override_path.chmod(readonly)

        # check/write policies.json
        policies_path = dist_dir / 'policies.json'
        if policies_path.exists():
            policies_path.touch(readwrite, exist_ok=True)
        file_hash = FirefoxConfig.hash_policies_json(policies_file=policies_path)
        dict_hash = FirefoxConfig.hash_policies_json()
        if file_hash != dict_hash:
            if policies_path.stat().st_mode != readwrite:
                policies_path.chmod(readwrite)
            policies_path.write_bytes(FirefoxConfig.parse_policies_json())
        if policies_path.stat().st_mode != readonly:
            policies_path.chmod(readonly)

        return await self.p.firefox.launch(
            executable_path=exe,
            args=['-override', f'"{str(override_path)}"'],
            headless=not __debug__,
            # devtools disabled in policies.json
            chromium_sandbox=False,
            # downloads_path and traces_dir are currently not, but can be set in policies.json
            downloads_path=Directory.BROWSER_DOWNLOADS,
            traces_dir=Directory.BROWSER_TRACES,
            firefox_user_prefs=FirefoxConfig.user_js,
        )

    async def schedule_task(self):
        if self.sheet_queue.empty():
            return
        if not hasattr(self, 'browser'):
            self.browser = await self.new_firefox()
        context = BrowserContext(self.p, self.browser)
        init_state = await self.sheet_queue.get()
        await context.start_from(init_state)
        task = CrawlerTask(self.p, context, self)
        task.register_self()
        task.schedule_self()


CrawlerTask.define_steps_in_strict_order  # TODO
