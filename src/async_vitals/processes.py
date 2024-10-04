"""Gerenciamento de processos do programa (criação, acesso aos objetos que os representam, etc)."""

from typing import Any, Callable, List, NamedTuple

from aioprocessing import AioProcess as AioProcessFactory
from aioprocessing.process import AioProcess
from multiprocessing import Event, Value

from src.uix.process_entrypoint import uix_process_entrypoint
from src.webdriver.process_entrypoint import webdriver_process_entrypoint
from src.async_vitals.messaging import ProgressStateNamespace, Queues, STR_DUMMY

__all__ = ["Fork"]


_Processes = NamedTuple(
    "_Processes",
    [
        ("uix", AioProcess),
        ("webdriver", AioProcess),
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

    started_event = Event()
    progress_values = Value(
        ProgressStateNamespace,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        STR_DUMMY,
        STR_DUMMY,
        STR_DUMMY,
        STR_DUMMY,
        STR_DUMMY,
    )

    return _Processes(
        uix=_run_proc(
            uix_process_entrypoint,
            Queues.arquivos_planilhas,
            started_event,
            progress_values,
        ),
        webdriver=_run_proc(
            webdriver_process_entrypoint,
            Queues.arquivos_planilhas,
            Queues.planilhas_prontas,
            started_event,
            progress_values,
        ),
        processes=_procs_list,
    )
