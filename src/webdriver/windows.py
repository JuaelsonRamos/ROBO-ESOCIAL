""" Operações que só funcionam na plataforma Windows."""

import ctypes as ct
import ctypes.wintypes as wintypes
from os.path import join
from pathlib import PurePath

from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome

from src.webdriver.local.io import PastasProjeto
from src.webdriver.utils.selenium import esperar_estar_presente

__all__ = ["bloquear_janela"]


def bloquear_janela(driver: Chrome) -> None:
    """ Bloqueia input de mouse e teclado à janela do chrome.

    :param driver: Instância do driver dono da janela deve ser bloqueada
    """
    # Referências:
    #   EnableWindow: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enablewindow
    #   GetWindowThreadProcessId: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowthreadprocessid
    #   EnumWindows: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows

    User32 = ct.cdll.User32
    CALLBACK = ct.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    url = f"file:///{PurePath(join(PastasProjeto.assets, 'loaded.html')).as_posix()}".encode()
    driver.get(url.decode())
    esperar_estar_presente(driver, (By.ID, "paginaCarregada"))

    def callback(hwnd: wintypes.HWND, lParam: wintypes.LPARAM) -> wintypes.BOOL:
        """ Função que vai ser executada para cada janela do windows.

        :param hwnd: ID da janela que é diferente do ID de processo
        :param lParam: Argumento arbritrário passado para essa função pela função envolvente
        """
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
    try:
        User32.EnumWindows(CALLBACK(callback), wintypes.LPARAM(driver.browser_pid))
    except TypeError:
        # LPARAM dá um erro que é automaticamente silenciado; não afeta o funcionamento
        pass
