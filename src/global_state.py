from __future__ import annotations

from src.gui.app import GraphicalRuntime
from src.sistema.crawl import BrowserRuntime
from src.types import TaskInitState

from asyncio import Queue
from dataclasses import dataclass
from tkinter import ttk

import sqlalchemy


@dataclass(frozen=True, slots=True)
class GlobalStateType:
    graphical_runtime: GraphicalRuntime
    browser_runtime: BrowserRuntime
    style: ttk.Style
    sqlite: sqlalchemy.Engine
    sheet_queue: Queue[TaskInitState]


_GlobalState: GlobalStateType = None  # type: ignore


def init_global_state(
    graphical_runtime: GraphicalRuntime, browser_runtime: BrowserRuntime
):
    global _GlobalState

    from src.db.client import init_sync_sqlite

    _GlobalState = GlobalStateType(
        graphical_runtime=graphical_runtime,
        browser_runtime=browser_runtime,
        style=ttk.Style(graphical_runtime.app),
        sqlite=init_sync_sqlite(),
        sheet_queue=browser_runtime.sheet_queue,
    )


def get_global_state() -> GlobalStateType:
    global _GlobalState
    return _GlobalState
