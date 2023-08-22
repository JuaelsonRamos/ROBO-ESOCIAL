"""Objetos que prossibilitam ou facilitam a comunicações entre unidades de concorrência (threads,
processos, coroutines)."""

from dataclasses import dataclass
from aioprocessing import AioQueue

__all__ = ["Queues"]


@dataclass(init=False, frozen=True)
class Queues:
    """Filas de acesso de dados entre diversas threads."""

    arquivos_planilhas = AioQueue()
    """Fila de arquivos de planilhas."""

    arquivos_nao_planilhas = AioQueue()
    """Fila de arquivos não-planilhas para serem removidos da pasta."""

    planilhas_prontas = AioQueue()
    """Fila de planilhas prontas esperando serem salvas."""

    planilhas_para_depois = AioQueue()
    """Fila de planilhas que deram erro no hora de salvar e o usuário optou por salvá-las depois."""
