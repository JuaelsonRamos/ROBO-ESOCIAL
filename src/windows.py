from __future__ import annotations

import win32api as api
import win32con as con


def get_monitor_settings():
    """Retorna `Iterable` de informações sobre os monitores conectados.

    :return: tuple de tuples no formato: (win32api._MonitorInfo, win32api.PyDEVMODEW)
    """
    monitors = [api.GetMonitorInfo(info[0]) for info in api.EnumDisplayMonitors()]
    as_devices = [
        api.EnumDisplaySettings(info['Device'], con.ENUM_CURRENT_SETTINGS)
        for info in monitors
    ]
    return tuple((mon, dev) for mon, dev in zip(monitors, as_devices))


def get_primary_monitor():
    monitors = [api.GetMonitorInfo(info[0]) for info in api.EnumDisplayMonitors()]
    for monitor in monitors:
        if monitor.Flag == con.MONITORINFOF_PRIMARY:
            return monitor
