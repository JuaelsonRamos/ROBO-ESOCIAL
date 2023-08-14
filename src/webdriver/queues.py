""" Filas de dados para co-rotinas.

Esse módulo deve ser importável por todos os outros módulo, então deve-se evitar dependências
circulares.
"""

from asyncio import Queue
from src.webdriver.tipos import PlanilhaPronta

arquivos_planilhas: Queue[str] = Queue()
""" Fila de arquivos de planilhas."""

arquivos_nao_planilhas: Queue[str] = Queue()
""" Fila de arquivos não-planilhas para serem removidos da pasta."""

planilhas_prontas: Queue[PlanilhaPronta] = Queue()
""" Fila de planilhas prontas esperando serem salvas."""

planilhas_para_depois: Queue[PlanilhaPronta] = Queue()
""" Fila de planilhas que deram erro no hora de salvar e o usuário optou por salvá-las depois."""
