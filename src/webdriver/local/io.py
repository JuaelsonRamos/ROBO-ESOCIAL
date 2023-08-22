"""Operações genéricas relacionadas ao sistema de arquivos do sistema operacional."""

import asyncio
import hashlib
import os
from dataclasses import dataclass
from os.path import abspath, dirname, join, basename
import re
from string import digits
import time
from typing import List, NamedTuple, Set
from pathlib import Path, PurePath
import shutil
import tkinter.messagebox as messagebox

from aioprocessing.queues import AioQueue
from src.webdriver.tipos import PlanilhaPronta, Int, ArquivoPlanilha
from src.webdriver.utils.python import string_multilinha

__all__ = [
    "PastasProjeto",
    "PastasSistema",
    "aguardar_antes_de_salvar",
    "buscar_planilhas",
    "criar_pastas_de_sistema",
    "remover_arquivos_nao_excel",
    "renomear_arquivo_existente",
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


regex_num_arquivo: re.Pattern[str] = re.compile(" \\[[0-9]+\\]$")
"""Regex para encontrar a porção do nome do arquivo que corresponde ao número de arquivos com o
mesmo nome."""


def renomear_arquivo_existente(dst_folder: str, src_file_path: str) -> str:
    """Checa se um arquivo com o mesmo nome já existe no diretório específicado; e se existe,
    retorna o nome de um arquivo que ainda não existe naquele diretório.

    :param dst_folder: Diretório de destino do novo arquivo cujo nome está sendo checado.
    :param src_file_path: Nome do arquivo fonte que deve ser renomeado caso outro já exista com o
        mesmo nome.
    :return: Nome de um arquivo que ainda não existe no diretório de destino (pode ser o mesmo nome
        especificado).
    """
    path: PurePath = PurePath(src_file_path)
    arquivos: List[str] = [x for x in os.listdir(dst_folder) if x.startswith(path.stem)]

    def new_path(p: PurePath, i: Int) -> str:
        return str(p.with_stem(p.stem + " [{}]".format(i)))

    if len(arquivos) == 0:
        return path.name
    if len(arquivos) == 1 and arquivos[0] == path.name:
        return new_path(path, Int(1))

    path = path.with_stem(path.stem.strip())
    num_match: List[re.Match[str] | None] = [
        regex_num_arquivo.search(PurePath(name).stem) for name in arquivos
    ]
    num_str: List[str] = [
        "".join([x for x in match.group(0) if x in digits])
        for match in num_match
        if match is not None
    ]
    num_int: List[Int] = [Int(i) for i in num_str]
    # Para uma list[int] não tem problema usar esse método,
    # mas para qualquer outra não dá pra confiar.
    num_int.sort()

    for random_int, ordered_int in zip(num_int, range(len(num_int))):
        if random_int != ordered_int + 1:
            # Se houver um buraco na ordem dos números aleatórios:
            # Exemplo random_int:  [1, 2, 4, 7, 9]
            # Exemplo ordered_int: [0, 1, 2, 3, 4]
            # 1 == 0+1, assim como 2 == 1+1, então pule esses
            # porém 4 != 2+1 então retorne 2+1, ou 3
            return new_path(path, Int(ordered_int + 1))

    # As duas listas estão em perfeita ordem:
    return new_path(path, Int(max(num_int) + 1))


ignore_arquivos: Set[str] = set()


def remover_arquivos_nao_excel(queue: AioQueue) -> None:
    """Espera arquivos não-excel serem encontrados e os move para fora da pasta de planilhas."""
    while True:
        file: ArquivoPlanilha = queue.get()
        nome_novo: str = renomear_arquivo_existente(PastasSistema.nao_excel, file.path)
        while True:
            try:
                if file.identifier in ignore_arquivos:
                    break
                if not file.isfile:
                    shutil.move(src=file.path, dst=join(PastasSistema.nao_excel, nome_novo))
                    break
                shutil.move(src=file.path, dst=join(PastasSistema.nao_excel, nome_novo))
            except PermissionError:
                mensagem_popup: bool = messagebox.askretrycancel(
                    "Tentando mover arquivo irrelevante!",
                    string_multilinha(
                        f"""
                        Arquivo Excel salvo! Porém, arquivos e pastas irrelevantes foram encontradas
                        em {PastasSistema.input} e um ERRO ocorreu ao tentar movê-los, pois, {file}
                        está aberto em outro programa. Clique REPETIR para tentar novamente ou CANCELAR
                        para pular este arquivo.
                        """.encode().decode()
                    ),
                )
                if mensagem_popup:
                    continue
                ignore_arquivos.add(file.identifier)
                break
            except FileNotFoundError:
                break
            else:
                break


def buscar_planilhas(queue_excel: AioQueue, queue_nao_excel: AioQueue) -> None:
    """Busca planilhas na pasta de planilhas e: as adiciona à fila de processamento ou espera 2 minutos antes de checar novamente caso não haja nenhuma."""
    ja_vistos: Set[str] = set()

    def folder_hash(path: str) -> bytes:
        stat_hash: Int = Int(hash(os.stat(path)))
        bytes_length: Int = Int((stat_hash.bit_length() + 7) // 8)
        stat_bytes: bytes = stat_hash.to_bytes(
            bytes_length, signed=(True if stat_hash < 0 else False)
        )
        return path.encode() + stat_bytes

    while True:
        arquivos: List[os.DirEntry[str]]
        ja_vistos_count: Int = Int(0)

        with os.scandir(PastasSistema.input) as folder:
            arquivos = list(folder)

        if len(arquivos) == 0:
            time.sleep(120)
            continue

        for arquivo in arquivos:
            arquivo_id: str
            try:
                if arquivo.is_file():
                    with open(arquivo.path, "rb") as file:
                        arquivo_id = hashlib.sha256(file.read()).hexdigest()
                else:
                    arquivo_id = hashlib.sha256(folder_hash(arquivo.path)).hexdigest()
            except FileNotFoundError:
                # Arquivo já foi processado e removido da pasta.
                continue

            if arquivo_id in ja_vistos:
                ja_vistos_count += Int(1)  # type: ignore
                continue
            if arquivo_id in ignore_arquivos:
                continue

            if (is_dir := arquivo.is_dir()) or Path(arquivo.path).suffix not in (".xlsx", ".xls"):
                arquivo_obj = ArquivoPlanilha(
                    isfile=(not is_dir), identifier=arquivo_id, path=arquivo.path
                )
                queue_nao_excel.put(arquivo_obj)
                ja_vistos.add(arquivo_id)
                continue

            # arquivo temporário criado quando a planilha é aberta
            if basename(arquivo.path).startswith("~$"):
                continue
            queue_excel.put(arquivo.path)
            ja_vistos.add(arquivo_id)
        if len(arquivos) == ja_vistos_count:
            time.sleep(120)


def aguardar_antes_de_salvar(queue: AioQueue, queue_para_depois: AioQueue) -> None:
    """Pega planilhas onde erros ocorreram na hora do salvamento e para cada uma espera uma
    quantidade determinada de tempo; depois as coloca novamente na fila de salvamento."""
    minutos: Int = Int(5)

    async def aguardar(planilha: PlanilhaPronta) -> None:
        await asyncio.sleep(minutos * 60)
        await queue.coro_put(planilha)

    async def criar_tarefas() -> None:
        while True:
            asyncio.create_task(aguardar(await queue_para_depois.coro_get()))

    asyncio.run(criar_tarefas())


def salvar_planilha_pronta(queue: AioQueue, queue_para_depois: AioQueue) -> None:
    """Espera planilhas ficarem prontas e as salva.

    Se um erro ocorrer o usuário tem a opção de salvar a planilha depois.
    """
    while True:
        nova_tabela = queue.get()
        nome_nova_planilha: str = renomear_arquivo_existente(PastasSistema.output, nova_tabela.name)
        novo_nome_arq_original: str = renomear_arquivo_existente(
            PastasSistema.pronto, nova_tabela.name
        )
        while True:
            try:
                nova_tabela.dataframe.to_excel(
                    join(PastasSistema.output, nome_nova_planilha),
                    index=False,
                    header=False,
                    engine="openpyxl",
                )
                shutil.move(
                    src=nova_tabela.original_path,
                    dst=join(PastasSistema.pronto, novo_nome_arq_original),
                )
            except PermissionError:
                mensagem_popup = messagebox.askretrycancel(
                    "Permissão negada!",
                    string_multilinha(
                        """
                        Não foi possível salvar o arquivo, pois, o programa não tem permissões o
                        suficiente. Isso também ocorre quando o arquivo já está aberto em outro
                        programa no momento do salvamento. Feche-o e tente novamente ou clique
                        CANCELAR para tentar mais tarde.
                        """
                    ),
                )
                if mensagem_popup:
                    continue
                queue_para_depois.put(nova_tabela)
                break
            except FileNotFoundError:
                break
            else:
                break
