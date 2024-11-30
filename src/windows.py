from __future__ import annotations

import os

from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace
from typing import Final, cast

import win32api as api
import win32con as con


_Monitor = namedtuple('_Monitor', ('MonitorInfo', 'DisplaySettings'))

APPDATA_DIR: Final[Path] = (
    Path('./__debug__/LocalAppData')
    if __debug__
    else Path(os.environ['LOCALAPPDATA']) / 'RoboEsocial'
)


def get_monitor_settings():
    """
    Retorna `Iterable` de informações sobre os monitores conectados.

    :return: tuple de namedtuples no formato: (win32api._MonitorInfo,
        win32api.PyDEVMODEW)
    """
    monitors = [
        api.GetMonitorInfo(cast(int, info[0])) for info in api.EnumDisplayMonitors()
    ]
    as_devices = [
        api.EnumDisplaySettings(info['Device'], con.ENUM_CURRENT_SETTINGS)
        for info in monitors
    ]
    return tuple(
        _Monitor(SimpleNamespace(**mon), dev) for mon, dev in zip(monitors, as_devices)
    )


def get_primary_monitor():
    for monitor in get_monitor_settings():
        if monitor.MonitorInfo.Flags | con.MONITORINFOF_PRIMARY:
            return monitor
