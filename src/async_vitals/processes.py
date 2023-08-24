"""Gerenciamento de processos do programa (criação, acesso aos objetos que os representam, etc)."""

from typing import Any, Callable, List, NamedTuple

from aioprocessing import AioProcess as AioProcessFactory
from aioprocessing.process import AioProcess
from src.async_vitals.messaging import Queues

from src.webdriver.local.io import (
    aguardar_antes_de_salvar,
    buscar_planilhas,
    remover_arquivos_nao_excel,
    salvar_planilha_pronta,
)
from src.webdriver.main import main

__all__ = ["Fork"]


_Processes = NamedTuple(
    "_Processes",
    [
        ("buscar_arquivos", AioProcess),
        ("remover_arquivos", AioProcess),
        ("salvar_arquivos", AioProcess),
        ("adiar_salvamento", AioProcess),
        ("main", AioProcess),
        ("processes", List[AioProcess]),
    ],
)
"""Definição da estrutura de acesso dos objetos que representam processos."""


def Fork() -> _Processes:
    """Função que inicia todos os processos.

    É necessário encapsular esse procedimento, pois, ele deve acontecer dentro de uma clausula 'if
    __name__' para prevenir criação de processos recursiva e para garantir que o processo mestre
    está completamente inicializado antes de criar outros.

    :return: Namedtuple com todos os processos acessíveis individualmente ou coletivamente em uma
        lista.
    """
    _procs_list: List[AioProcess] = []

    def _run_proc(func: Callable[..., Any], *args: Any, **kwargs: Any) -> AioProcess:
        p = AioProcessFactory(name=func.__name__, target=func, args=(*args,), kwargs=kwargs)
        p.start()
        _procs_list.append(p)
        return p

    return _Processes(
        buscar_arquivos=_run_proc(
            buscar_planilhas, Queues.arquivos_planilhas, Queues.arquivos_nao_planilhas
        ),
        remover_arquivos=_run_proc(remover_arquivos_nao_excel, Queues.arquivos_nao_planilhas),
        salvar_arquivos=_run_proc(
            salvar_planilha_pronta, Queues.planilhas_prontas, Queues.planilhas_para_depois
        ),
        adiar_salvamento=_run_proc(
            aguardar_antes_de_salvar, Queues.planilhas_prontas, Queues.planilhas_para_depois
        ),
        main=_run_proc(main, Queues.arquivos_planilhas, Queues.planilhas_prontas),
        processes=_procs_list,
    )
