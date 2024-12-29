from __future__ import annotations

from src.gui.lock import TkinterLock
from src.gui.widgets.StatusBar.ProgressCounter import ProgressCounter
from src.gui.widgets.StatusBar.StatusBar import StatusBar
from src.gui.widgets.ViewNavigator import LazyButton, LazyViewNavigator
from src.runtime import CommandLineArguments
from src.windows import get_monitor_settings

import math
import tkinter as tk


class CertificateButton(LazyButton):
    text = 'Certificados'

    def lazy_load_python_modules(self) -> None:
        from src.gui.views.CertificateManager import CertificateManager

        self._view_widget = CertificateManager


class SheetProcessButton(LazyButton):
    text = 'Processar'

    def lazy_load_python_modules(self) -> None:
        from src.gui.views.SheetProcess import SheetProcess

        self._view_widget = SheetProcess


class HistoryButton(LazyButton):
    text = 'Histórico'


class VisualizeButton(LazyButton):
    text = 'Visualizar'


class ToolsButton(LazyButton):
    text = 'Ferramentas'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.anchor(tk.W)
        self.geometry('1280x720')
        self.title('ROBO-ESOCIAL')
        self.create_widgets()
        self.propagate(tk.FALSE)
        self._exit_flag: bool = False
        self._quit_flag: bool = False
        self._render_lock = TkinterLock
        self.fps, self.frametime = self._calc_monitor_frametimes()

        self.protocol('WM_DELETE_WINDOW', self.schedule_quit)

    def create_widgets(self):
        # Adicionar primeiro para que as dimensões tenham precedência sob as outras
        status_bar = StatusBar(self)
        ProgressCounter(
            status_bar,
            idle='Aguardando Processamento',
            template='Processando Planilhas ({current}/{total})',
        )
        view_nav = LazyViewNavigator(self)
        view_nav.pack()
        view_nav.add_button(CertificateButton, invoke=True)
        view_nav.add_button(SheetProcessButton)
        view_nav.add_button(HistoryButton)
        view_nav.add_button(VisualizeButton)
        view_nav.add_button(ToolsButton)

    def schedule_quit(self) -> None:
        """Deletes and kills Tcl's interpreter on next tick."""
        self._quit_flag = True

    def has_quit(self) -> bool:
        return self._exit_flag

    def tick(self) -> None:
        if self._exit_flag:
            return
        if self._quit_flag:
            self.quit()
            self.destroy()
            self._exit_flag = True
            return
        if self._render_lock.locked():
            return
        self.update_idletasks()
        self.update()

    def _calc_monitor_frametimes(self) -> tuple[int, float]:
        """Returns tuple (FPS, Frametime)"""
        monitors_fps: list[int | float] = [
            monitor.DisplaySettings.DisplayFrequency
            for monitor in get_monitor_settings()
        ]
        best_device_fps: int = math.ceil(max(monitors_fps))
        app_fps: int = best_device_fps if 15 <= best_device_fps <= 75 else 60
        app_tick: float = 1 / app_fps  # miliseconds
        app_tick = float(f'{app_tick:.4f}')
        return (app_fps, app_tick)


class GraphicalRuntime:
    cli_args = CommandLineArguments().parse_argv()

    def __init__(self) -> None:
        self.app = App()

    def should_run(self) -> bool:
        return not self.cli_args.no_tkinter
