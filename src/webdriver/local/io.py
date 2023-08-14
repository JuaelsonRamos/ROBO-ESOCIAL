"""Operações genéricas relacionadas ao sistema de arquivos do sistema operacional."""

import asyncio
import os
from dataclasses import dataclass
from os.path import abspath, dirname, join, basename, isdir
from typing import List, NamedTuple, Set
from pathlib import Path
import shutil
import tkinter.messagebox as messagebox
from src.webdriver.queues import (
    arquivos_planilhas,
    arquivos_nao_planilhas,
    planilhas_prontas,
    planilhas_para_depois,
)
from src.webdriver.tipos import PlanilhaPronta, Int

__all__ = [
    "PastasProjeto",
    "PastasSistema",
    "aguardar_antes_de_salvar",
    "buscar_planilhas",
    "criar_pastas_de_sistema",
    "remover_arquivos_nao_excel",
    "salvar_planilha_pronta",
]

PastasSistema = NamedTuple(
    "PastasSistema", [("input", str), ("output", str), ("pronto", str), ("nao_excel", str)]
)(
    "C:\\SISTEMA_PLANILHAS",
    "C:\\SISTEMA_PLANILHAS_PROCESSADAS",
    "C:\\SISTEMA_PLANILHAS_ARQUIVADAS",
    "C:\\SISTEMA_LIXEIRA",
)
"""Lista de pastas do sistema que o programa utiliza."""


def criar_pastas_de_sistema() -> None:
    """Cria as pastas que o programa vai utilizar para guardar dados importantes."""
    for pasta in PastasSistema:
        try:
            os.mkdir(pasta)
        except FileExistsError:
            pass


@dataclass(init=False, frozen=True)
class PastasProjeto:
    """Pastas relacionadas ao próprio projeto (código fonte).

    :final:
    """

    root: str = abspath(join(dirname(__file__), "..", "..", ".."))
    assets: str = join(root, "assets")


ignore_arquivos: Set[str] = set()


async def remover_arquivos_nao_excel() -> None:
    """Espera arquivos não-excel serem encontrados e os move para fora da pasta de planilhas."""
    while True:
        caminho: str = await arquivos_nao_planilhas.get()
        while True:
            try:
                if caminho in ignore_arquivos:
                    break
                if isdir(caminho):
                    shutil.move(src=caminho, dst=PastasSistema.nao_excel)
                    break
                shutil.move(src=caminho, dst=join(PastasSistema.nao_excel, basename(caminho)))
            except PermissionError:
                mensagem_popup: bool = messagebox.askretrycancel(
                    "Tentando mover arquivo irrelevante!",
                    f"Arquivo Excel salvo! Porém, arquivos e pastas irrelevantes foram encontradas em {PastasSistema.input} e um ERRO ocorreu ao tentar movê-los, pois, {caminho} está aberto em outro programa. Clique REPETIR para tentar novamente ou CANCELAR para pular este arquivo.".encode().decode(),
                )
                if mensagem_popup:
                    continue
                ignore_arquivos.add(caminho)
                break
            except FileNotFoundError:
                break
            else:
                break

async def buscar_planilhas() -> None:
    """Busca planilhas na pasta de planilhas e: as adiciona à fila de processamento ou espera 2 minutos antes de checar novamente caso não haja nenhuma."""
    asyncio.create_task(remover_arquivos_nao_excel())
    ja_vistos: Set[str] = set()
    while True:
        arquivos: List[os.DirEntry[str]] = list(os.scandir(PastasSistema.input))
        ja_vistos_count: Int = Int(0)
        if len(arquivos) == 0:
            await asyncio.sleep(120)
            continue
        for arquivo in arquivos:
            if arquivo.path in ja_vistos:
                ja_vistos_count += Int(1)  # type: ignore
                continue
            if arquivo.path in ignore_arquivos:
                continue
            if arquivo.is_dir() or Path(arquivo.path).suffix not in (".xlsx", ".xls"):
                await arquivos_nao_planilhas.put(arquivo.path)
                ja_vistos.add(arquivo.path)
                continue
            # arquivo temporário criado quando a planilha é aberta
            if basename(arquivo.path).startswith("~$"):
                continue
            await arquivos_planilhas.put(arquivo.path)
            ja_vistos.add(arquivo.path)
        if len(arquivos) == ja_vistos_count:
            await asyncio.sleep(120)


async def aguardar_antes_de_salvar() -> None:
    """Pega planilhas onde erros ocorreram na hora do salvamento e para cada uma espera uma
    quantidade determinada de tempo; depois as coloca novamente na fila de salvamento."""
    minutos: Int = Int(5)

    async def aguardar(planilha: PlanilhaPronta) -> None:
        await asyncio.sleep(minutos * 60)
        await planilhas_prontas.put(planilha)

    while True:
        asyncio.create_task(aguardar(await planilhas_para_depois.get()))

async def salvar_planilha_pronta() -> None:
    """Espera planilhas ficarem prontas e as salva.

    Se um erro ocorrer o usuário tem a opção de salvar a planilha depois.
    """
    asyncio.create_task(aguardar_antes_de_salvar())
    while True:
        nova_tabela = await planilhas_prontas.get()
        while True:
            try:
                nova_tabela.dataframe.to_excel(
                    join(PastasSistema.output, nova_tabela.name),
                    index=False,
                    header=False,
                    engine="openpyxl",
                )
                shutil.move(
                    src=nova_tabela.original_path,
                    dst=join(PastasSistema.pronto, nova_tabela.name),
                )
            except PermissionError:
                mensagem_popup = messagebox.askretrycancel(
                    "Permissão negada!",
                    "Não foi possível salvar o arquivo, pois, o programa não tem permissões o suficiente. Isso também ocorre quando o arquivo já está aberto em outro programa no momento do salvamento. Feche-o e tente novamente ou clique CANCELAR para tentar mais tarde.",
                )
                if mensagem_popup:
                    continue
                await planilhas_para_depois.put(nova_tabela)
                break
            except FileNotFoundError:
                break
            else:
                break
