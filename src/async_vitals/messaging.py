"""Objetos que prossibilitam ou facilitam a comunicações entre unidades de concorrência (threads,
processos, coroutines)."""

from ctypes import Structure, c_int32, c_long, c_longlong, string_at, sizeof, memmove
from aioprocessing import AioQueue
from dataclasses import dataclass

__all__ = [
    "ProgressStateNamespace",
    "Queues",
    "STR_BASE_TYPE",
    "STR_BUFSIZE",
    "STR_DUMMY",
    "STR_TYPE",
]


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


STR_BUFSIZE: int = 1024
STR_BASE_TYPE = c_int32
STR_TYPE = STR_BASE_TYPE * STR_BUFSIZE
STR_DUMMY = STR_TYPE(*([ord("\0")] * 10))


class ProgressStateNamespace(Structure):
    # See: https://stackoverflow.com/a/5352531/15493645

    _fields_ = [
        ("cnpj_last_updated_ns", c_longlong),
        ("cnpj_max_last_updated_ns", c_longlong),
        ("cnpj_current", c_long),
        ("cnpj_max", c_long),
        ("cpf_last_updated_ns", c_longlong),
        ("cpf_max_last_updated_ns", c_longlong),
        ("cpf_current", c_long),
        ("cpf_max", c_long),
        ("cnpj_msg", STR_TYPE),
        ("cnpj_long_msg", STR_TYPE),
        ("cpf_msg", STR_TYPE),
        ("cpf_long_msg", STR_TYPE),
        ("general_msg", STR_TYPE),
    ]

    @classmethod
    def get_string(cls, value: STR_TYPE) -> str:
        return string_at(value, sizeof(value)).decode("utf-32").replace("\0", "")

    @classmethod
    def set_string(cls, original_value: STR_TYPE, value: str | STR_TYPE) -> None:
        size = len(value)
        if size > STR_BUFSIZE:
            raise ValueError("String é muito grande para o buffer.")
        memmove(
            original_value,
            value
            if isinstance(value, STR_TYPE)
            else (STR_BASE_TYPE * size)(*[ord(c) for c in value]),
            sizeof(STR_BASE_TYPE) * size,
        )
