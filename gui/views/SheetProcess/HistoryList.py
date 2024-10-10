from __future__ import annotations

import gui.views.SheetProcess.data as data

from gui.views.SheetProcess.InteractiveTreeList import InteractiveTreeList


class HistoryList(InteractiveTreeList):
    def __init__(self, master):
        super().__init__(master, 'Histórico', columns=data.history.columns)
        self.add_button('Exportar Planilha')
        self.add_button('Exportar Histórico')
