"""Entrypoint da parte da aplicação relacionada ao WebDriver."""

from pathlib import Path
import time
from aioprocessing.queues import AioQueue

import pandas as pd
from typing import Iterable, Any, cast
from os.path import basename

from src.webdriver.acesso import processar_planilha
from src.local.io import criar_pastas_de_sistema
from src.webdriver.types import PlanilhaPronta
from src.async_vitals.messaging import ProgressStateNamespace as progress_values_t, STR_DUMMY
from src.webdriver.planilha import (
    DELTA,
    ColunaPlanilha,
    checar_cpfs_cnpjs,
    registro_de_dados_relevantes,
)

__all__ = ["main"]


def main(
    queue_planilhas: AioQueue,
    queue_prontas: AioQueue,
    started_event: object,
    progress_values: object,
) -> None:
    """Entrypoint da aplicação."""
    criar_pastas_de_sistema()
    while True:
        caminho_arquivo_excel: str = queue_planilhas.get()
        started_event.set()
        tabela: pd.DataFrame
        if Path(caminho_arquivo_excel).suffix == ".xls":
            tabela = pd.read_excel(caminho_arquivo_excel, header=None, engine="xlrd")
        else:
            tabela = pd.read_excel(caminho_arquivo_excel, header=None, engine="openpyxl")

        coluna_cnpj_unidade = cast(
            Iterable[Any], tabela.iloc[DELTA:, ColunaPlanilha.CNPJ_UNIDADE].values
        )
        coluna_cnpj = cast(Iterable[Any], tabela.iloc[DELTA:, ColunaPlanilha.CNPJ].values)
        coluna_cpf = cast(Iterable[Any], tabela.iloc[DELTA:, ColunaPlanilha.CPF].values)
        coluna_cnpj_nomes = cast(Iterable[Any], tabela.iloc[DELTA:, ColunaPlanilha.NOME_UNIDADE])
        coluna_cpf_nomes = cast(Iterable[Any], tabela.iloc[DELTA:, ColunaPlanilha.NOME_FUNCIONARIO])

        checar_cpfs_cnpjs(coluna_cpf, coluna_cnpj, coluna_cnpj_unidade)

        funcionarios = registro_de_dados_relevantes(
            coluna_cnpj_unidade, coluna_cnpj, coluna_cpf, coluna_cnpj_nomes, coluna_cpf_nomes
        )
        with progress_values.get_lock():
            progress_values.cnpj_max = len(funcionarios.CNPJ_lista)
            progress_values.cpf_max = len(funcionarios.CPF_lista)
            progress_values.cnpj_max_last_updated_ns = time.time_ns()
            progress_values.cpf_max_last_updated_ns = time.time_ns()

        dataframe: pd.DataFrame = processar_planilha(funcionarios, tabela, progress_values)

        with progress_values.get_lock():
            progress_values.cnpj_max = 0
            progress_values.cpf_max = 0
            progress_values.cnpj_max_last_updated_ns = time.time_ns()
            progress_values.cpf_max_last_updated_ns = time.time_ns()
            progress_values.cnpj_current = 0
            progress_values.cpf_current = 0
            progress_values.cnpj_last_updated_ns = time.time_ns()
            progress_values.cpf_last_updated_ns = time.time_ns()
            progress_values_t.set_string(progress_values.cnpj_msg, STR_DUMMY)
            progress_values_t.set_string(progress_values.cpf_msg, STR_DUMMY)
            progress_values_t.set_string(progress_values.cnpj_long_msg, STR_DUMMY)
            progress_values_t.set_string(progress_values.cpf_long_msg, STR_DUMMY)

        queue_prontas.put(
            PlanilhaPronta(dataframe, basename(caminho_arquivo_excel), caminho_arquivo_excel)
        )

        started_event.clear()
