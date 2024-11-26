from __future__ import annotations

import src.gui.views.SheetProcess.data as data

from src.gui.views.SheetProcess.InteractiveTreeList import InteractiveTreeList


class HistoryList(InteractiveTreeList):
    def __init__(self, master):
        super().__init__(master, 'Histórico', columns=data.HISTORY)
        self.add_button('Exportar Planilha')
        self.add_button('Exportar Histórico')
