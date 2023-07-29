import ctypes as ct
import ctypes.wintypes as wintypes
from undetected_chromedriver import Chrome

def bloquear_janela(driver: Chrome) -> None:
    """Bloqueia input de mouse e teclado à janela do chrome."""
    # Referências:
    #   EnableWindow: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enablewindow
    #   GetWindowThreadProcessId: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowthreadprocessid
    #   EnumWindows: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows

    User32 = ct.cdll.User32
    CALLBACK = ct.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, lParam) -> bool:
        pid = wintypes.DWORD(0)
        User32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ct.POINTER(wintypes.DWORD)]
        User32.GetWindowThreadProcessId.restype = wintypes.DWORD
        User32.GetWindowThreadProcessId(hwnd, ct.byref(pid))
        if pid.value == lParam:
            User32.EnableWindow.argtypes = [wintypes.HWND, wintypes.BOOL]
            User32.EnableWindow.restype = wintypes.BOOL
            User32.EnableWindow(hwnd, False)

        return wintypes.BOOL(1)

    User32.EnumWindows.argtypes = [CALLBACK, wintypes.LPARAM]
    User32.EnumWindows.restype = wintypes.BOOL
    # LPARAM dá um erro que é automaticamente silenciado; não afeta o funcionamento
    User32.EnumWindows(CALLBACK(callback), wintypes.LPARAM(driver.browser_pid))