from __future__ import annotations

import io
import os
import sys
import string
import functools

from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import (
    Callable,
    Final,
    Iterable,
    Literal,
    NamedTuple,
    Sequence,
    cast,
    overload,
)

import win32api as api
import win32con as con
import win32gui as gui
import win32file as file
import pywintypes  # must be imported first to avoid error with pywin32's version

from win32.lib import pywintypes
from win32comext.shell import shell, shellcon


_Monitor = namedtuple('_Monitor', ('MonitorInfo', 'DisplaySettings'))

APPDATA_DIR: Final[Path] = (
    Path('./__debug__/LocalAppData')
    if __debug__
    else Path(os.environ['LOCALAPPDATA']) / 'RoboEsocial'
)

if not APPDATA_DIR.exists():
    APPDATA_DIR.mkdir(mode=0o750, parents=True, exist_ok=False)


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


def open_file_dialog(
    hwnd: int,
    title: str,
    extensions: Sequence[tuple[str, tuple[str, ...]]],
    initial_dir: Path | None = None,
    default_extension: int = 0,
    multi_select: bool = False,
    file_must_exist: bool = True,
    path_must_exist: bool = True,
    allow_read_only: bool = True,
    hide_network_button: bool = True,
    confirm_overwrite: bool = True,
) -> tuple[Path, ...]:
    # NOTE If the HWND doesn't belong to the same process, HINSTANCE is useless.
    # Source: https://stackoverflow.com/q/9045594/15493645
    # From comment:
    # > The top window may not belong to your process, so its instance handle is
    # > useless to you.
    h_instance: int | None = None

    flags: int = con.OFN_EXPLORER | con.OFN_NOCHANGEDIR
    if multi_select:
        flags |= con.OFN_ALLOWMULTISELECT
    if file_must_exist:
        flags |= con.OFN_FILEMUSTEXIST
    if path_must_exist:
        flags |= con.OFN_PATHMUSTEXIST
    if not allow_read_only:
        flags |= con.OFN_NOREADONLYRETURN
    if hide_network_button:
        flags |= con.OFN_NONETWORKBUTTON
    if confirm_overwrite:
        flags |= con.OFN_OVERWRITEPROMPT

    # type checking extensions object
    if len(extensions) == 0:
        raise ValueError('empty file extension sequence')
    for ext in extensions:
        if not isinstance(ext, tuple):
            raise TypeError(f'{type(ext).__name__=} expected tuple')
        if len(ext) != 2:
            raise ValueError(f'{len(ext)=} expected 2')
        name: str = ext[0]
        file_suffixes: tuple[str, ...] = ext[1]
        if not isinstance(name, str):
            raise TypeError(f'{type(ext[0]).__name__=} expected str')
        if not isinstance(file_suffixes, tuple):
            raise TypeError(f'{type(ext[1]).__name__=} expected tuple')
        if len(file_suffixes) == 0:
            raise ValueError('empty tuple of file extensions')
        for i, suffix in enumerate(file_suffixes):
            if isinstance(suffix, str):
                continue
            raise ValueError(f'{type(file_suffixes[i]).__name__=} expected str')

    # parsing extension object
    filter: str
    NULL = '\0'
    with io.StringIO() as buffer:
        for ext in extensions:
            name: str = ext[0].strip(string.whitespace)
            buffer.write(name)
            # name and suffixes are separated by a NULL character
            buffer.write(NULL)
            suffixes: str = ';'.join(suffix.upper() for suffix in ext[1])
            buffer.write(suffixes)
            # pairs (name, suffixes) are separated by a NULL character as well
            buffer.write(NULL)
        # filter sequence must end with 2 NULL characters
        buffer.write(NULL)
        filter = buffer.getvalue()

    if default_extension < 0:
        raise ValueError(f'{default_extension=} expected >= zero')
    # variable value is zero-based, but argument expects 1-based index
    default_extension += 1

    starting_dir: str | None = None
    if isinstance(initial_dir, Path):
        starting_dir = str(initial_dir)

    # 256 is the minimum
    buffer_size: int = 256 * 10

    # GetOpenFileNameW may change working dir of the process it runs in. Specifying the
    # "do not change working dir" flag doesn't prevent it from doing so while the window
    # is open, which in this case is not a problem since python's GIL effectively blocks
    # the whole process (threads and coroutines) during the execution.
    #
    # Anyways, storing the current working dir before and setting it afterwards is too
    # litle of a cost for a "just to be sure" type of action.
    cwd = os.getcwd()
    try:
        # tuple in the form ('paths spec', 'CustomFilter argument', 'Flags argument')
        result: tuple[str, str | None, int]
        result = gui.GetOpenFileNameW(
            hwndOwner=hwnd,
            hInstance=h_instance,
            Flags=flags,
            Title=title,
            InitialDir=starting_dir,
            FilterIndex=default_extension,
            Filter=filter,
            MaxFile=buffer_size,
            CustomFilter=None,
            DefExt=None,
            File=None,
            TemplateName=None,
        )
        # NULL separated sequence (string) where the first item is a directory path, and
        # all the others are relative filenames, unless only one file was selected, in
        # which case the whole string is an absolute path.
        path_spec: str = result[0].strip(NULL)
        if NULL not in path_spec:
            # single absolute path
            return (Path(path_spec),)
        path_spec_iterable: list[str] = path_spec.split(NULL)
        dir: str = path_spec_iterable.pop(0)
        return tuple(Path(dir, file_name) for file_name in path_spec_iterable)
    except pywintypes.error as err:
        raise RuntimeError(
            f'win32 error: {err.winerror=}, {err.funcname=}, {err.strerror=}'
        )
    finally:
        os.chdir(cwd)
