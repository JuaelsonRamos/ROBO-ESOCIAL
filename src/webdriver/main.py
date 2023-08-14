"""Entrypoint da parte da aplicação relacionada ao WebDriver."""

import asyncio
from pathlib import Path

import pandas as pd
from typing import Iterable, Any, cast
from os.path import basename

from src.webdriver.acesso import processar_planilha
from src.webdriver.local.io import criar_pastas_de_sistema, buscar_planilhas, salvar_planilha_pronta
from src.webdriver.queues import arquivos_planilhas, planilhas_prontas
from src.webdriver.tipos import PlanilhaPronta
from src.webdriver.planilha import (
    DELTA,
    ColunaPlanilha,
    checar_cpfs_cnpjs,
    registro_de_dados_relevantes,
)

__all__ = ["main"]


async def main() -> None:
    """Entrypoint da aplicação."""
    criar_pastas_de_sistema()
    asyncio.create_task(buscar_planilhas())
    asyncio.create_task(salvar_planilha_pronta())
    while True:
        caminho_arquivo_excel = await arquivos_planilhas.get()
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

        checar_cpfs_cnpjs(coluna_cpf, coluna_cnpj, coluna_cnpj_unidade)

        funcionarios = registro_de_dados_relevantes(coluna_cnpj_unidade, coluna_cnpj, coluna_cpf)

        dataframe: pd.DataFrame = processar_planilha(funcionarios, tabela)
        await planilhas_prontas.put(
            PlanilhaPronta(dataframe, basename(caminho_arquivo_excel), caminho_arquivo_excel)
        )
