from __future__ import annotations

import os
import functools

from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Final, Literal, NamedTuple, cast, overload

import win32api as api
import win32con as con
import win32file as file

from win32comext.shell import shell, shellcon


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


@dataclass(frozen=True, slots=True)
class WindowsDriveUINames:
    FullName: str
    DisplayName: str
    ParsingLetter: str


def get_drive_shell_names(path: str, /) -> WindowsDriveUINames:
    """
    Takes drive path as in `'C:\\'` and return the drive's UI displayed name as Windows
    shows it in File Explorer or wherever it needs a display name when the label is
    empty.

    Drive labels can be empty, which mean they have not been set by the system nor user,
    but File Explorer always has a label to show and it seem to vary according to the
    system language, just like the default user folder's names do. This function
    retrieves such names.

    Returns an namespace object. For `path='C:\\'` the return object looks like:
    ```
    WindowsDriveUINames(
        FullName='Local Disk (C:)',
        DisplayName='Local Disk',
        ParsingLetter='C:',
    )
    ```

    This function may block execution for taking took long to retrieve information in
    case there is a problem with the user's device or system. Defective drives tend to
    cause this problem even under the native File Explorer.

    See:
    * `C# Implementation Reference <impl>`_
    * `SHParseDisplayName function (shlobj_core.h) <SHParseDisplayName>`_
    * `SHGetNameFromIDList function (shobjidl_core.h) <SHGetNameFromIDList>`_

    .. _impl: https://stackoverflow.com/a/29198314/15493645
    .. _SHParseDisplayName: https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shparsedisplayname
    .. _SHGetNameFromIDList: https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-shgetnamefromidlist
    """
    pidl: list[bytes]
    pidl, _ = shell.SHParseDisplayName(path, 0)
    get_name: Callable[[int], str] = functools.partial(shell.SHGetNameFromIDList, pidl)
    full_name: str = get_name(shellcon.SIGDN_PARENTRELATIVE)
    display_name: str = get_name(pidl, shellcon.SIGDN_PARENTRELATIVEEDITING)
    parsing_letter: str = get_name(pidl, shellcon.SIGDN_PARENTRELATIVEPARSING)
    return WindowsDriveUINames(
        FullName=full_name, DisplayName=display_name, ParsingLetter=parsing_letter
    )


@dataclass(frozen=True, slots=True)
class WindowsDrive:
    Path: str
    Letter: str
    IsRemovable: bool
    IsFixed: bool
    FileSystem: str

    __unsafe_ref = SimpleNamespace(ui_names=None)

    @property
    def UINames(self) -> WindowsDriveUINames:
        """Lazy loading property to try and mitigate the thread blocking problem of
        retrieving this data.
        """
        if self.__unsafe_ref.ui_names is None:
            self.__unsafe_ref.ui_names = get_drive_shell_names(self.Path)
        return self.__unsafe_ref.ui_names


def get_logical_drives() -> tuple[WindowsDrive, ...]:
    drives: list[str] = api.GetLogicalDriveStrings().strip('\0').split('\0')
    result: list[WindowsDrive] = []
    for path in drives:
        _type: int = file.GetDriveType(path)
        info: tuple[str, int, int, int, str] = api.GetVolumeInformation(path)
        result.append(
            WindowsDrive(
                Path=path,
                Letter=path.removesuffix(':\\'),
                IsRemovable=_type is file.DRIVE_REMOVABLE,
                IsFixed=_type is file.DRIVE_FIXED,
                FileSystem=info[-1],
            )
        )
    return tuple(result)
