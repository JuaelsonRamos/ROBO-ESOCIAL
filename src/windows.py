import ctypes as ct
import ctypes.wintypes as wintypes
from hashlib import sha512
from undetected_chromedriver import Chrome

def bloquear_janela(driver: Chrome) -> None:
    """Bloqueia input de mouse e teclado à janela do chrome."""
    # Referências:
    #   EnableWindow: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enablewindow
    #   GetWindowTextW: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowtextw
    #   EnumWindows: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows
    #   Passar pointer de string: https://stackoverflow.com/a/10905155/15493645

    User32 = ct.cdll.User32
    driver.get("about:blank") # para que o site não mude o titulo
    titulo: str = sha512(bytes(str(driver.current_window_handle), "utf-8")).hexdigest()
    driver.execute_script(f"document.title = '{titulo}'")

    CALLBACK = ct.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, lParam) -> bool:
        str_pointer = ct.create_unicode_buffer(255)
        User32.GetWindowTextW.argtypes = [ct.c_void_p, ct.c_wchar_p, ct.c_int]
        User32.GetWindowTextW.restype = ct.c_int
        bytes_lidos: int = User32.GetWindowTextW(hwnd, str_pointer, ct.sizeof(str_pointer))
        if bytes_lidos == 0:
            # muitas coisas da interface gráfica além dos programas abertos pelo
            # usuario contam como janelas, portanto, o titulo de algumas podem estar em branco
            pass
        elif titulo in str_pointer.value:
            User32.EnableWindow.argtypes = [wintypes.HWND, wintypes.BOOL]
            User32.EnableWindow.restype = wintypes.BOOL
            User32.EnableWindow(hwnd, False)

        return wintypes.BOOL(1)

    User32.EnumWindows.argtypes = [CALLBACK, wintypes.LPARAM]
    User32.EnumWindows.restype = wintypes.BOOL
    # LPARAM como None dá um erro que é automaticamente silenciado; não afeta o funcionamento
    User32.EnumWindows(CALLBACK(callback), None)