""" Operações de manipulação de planilhas, processamento de dados que vem de planilhas e dados
relevantes para interações complanilhas."""

import re
from dataclasses import dataclass, field
from math import isnan
from string import ascii_letters
from typing import Any, Iterable, List, Dict
from src.webdriver.tipos import Int

__all__ = [
    "ColunaPlanilha",
    "DELTA",
    "RegistroCPF",
    "RegistroDados",
    "celulas_preenchidas",
    "checar_cpfs_cnpjs",
    "filtrar_cpfs_apenas_matriz",
    "letra_para_numero_coluna",
    "registro_de_dados_relevantes",
]

DELTA = Int(2)
""" Quantidade de linhas da planilha a serem ignoradas de cima para baixo."""


def letra_para_numero_coluna(char: str) -> Int:
    """Retorna o número correspondente a uma lista de letras em formato de index para o pandas.

    Exemplo: ``'L' == 12``, portanto esta função retorna 11 (12-1).

    :param char: String de caracteres minúsculos ou maiúsculos dentro do alfabeto.
    """
    num = Int(0)
    for c in char:
        if c in ascii_letters:
            num = Int(num * 26 + (ord(c.upper()) - ord("A")) + 1)
    return Int(num - 1)


@dataclass(init=False, frozen=True)
class ColunaPlanilha:
    """Registro de coordenadas numéricas (otimizadas para indexação de listas) de certas colunas da
    planilha.

    :final:
    """

    SITUACAO: Int = letra_para_numero_coluna("L")
    NASCIMENTO: Int = letra_para_numero_coluna("J")
    DEMISSAO: Int = letra_para_numero_coluna("N")
    MATRICULA: Int = letra_para_numero_coluna("G")
    ADMISSAO: Int = letra_para_numero_coluna("M")
    CPF: Int = letra_para_numero_coluna("T")
    CNPJ_UNIDADE: Int = letra_para_numero_coluna("AM")
    CNPJ: Int = letra_para_numero_coluna("BC")


# catalogando cpf para cada cnpj
@dataclass(init=True, frozen=True)
class RegistroCPF:
    """Dados relevantes ao CPF do funcionário e informações da posição do CPF na planilha.

    :final:
    :param CPF: CPF do funcionário com pontuação.
    :param linha: Posição vertical do CPF.
    """

    # cpf com pontuação
    CPF: str
    linha: Int


@dataclass(init=True, frozen=True)
class RegistroDados:
    """Dados da empresa que são relevantes a raspagem de dados.

    :final:
    :param CNPJ_lista: Lista de CNPJs com pontuação.
    :param CPF_lista: Lista onde cada objeto contém informações sobre o CPF de um funcionário.
    """

    CNPJ_lista: List[str] = field(init=False, default_factory=list)
    CPF_lista: List[RegistroCPF] = field(init=False, default_factory=list)


# ESSA FUNÇÃO NÃO ESTÁ MAIS SENDO USADA; MANTIDA AQUI CASO MUDE DE IDEA
def filtrar_cpfs_apenas_matriz(
    coluna_cnpj: Iterable[str], coluna_cpf: Iterable[str]
) -> Dict[str, List[RegistroCPF]]:
    """Cria um dicionário apenas com os cnpjs da matriz e os cpfs correspondentes a esses cpnjs.

    :param coluna_cnpj: Coluna da planilha com todos os CNPJs da matriz.
    :param coluna_cpf: Coluna da planilha com todos os CPFs de funcionários.
    :return: Dicionário onde as chaves são CNPJs da matriz e os valores são listas de CPFs que -- na
        planilha -- aparecem na mesma linha que aquele CNPJ.
    """
    CATALOGO_FUNCIONARIOS: Dict[str, List[RegistroCPF]] = {}
    for index, info in enumerate(zip(coluna_cnpj, coluna_cpf)):
        pos_linha = Int(DELTA + index)
        CNPJ, CPF = info
        if not re.split("[\\/-]", CNPJ)[1] == "0001":
            continue
        if not CNPJ in CATALOGO_FUNCIONARIOS:
            CATALOGO_FUNCIONARIOS[CNPJ] = [RegistroCPF(CPF=CPF, linha=pos_linha)]
        else:
            CATALOGO_FUNCIONARIOS[CNPJ].append(RegistroCPF(CPF=CPF, linha=pos_linha))

    return CATALOGO_FUNCIONARIOS


def registro_de_dados_relevantes(
    coluna_cnpj_unidade: Iterable[str], coluna_cnpj: Iterable[str], coluna_cpf: Iterable[str]
) -> RegistroDados:
    """Cria um registro de todos os cpnjs da MATRIZ e TODOS os cpfs.

    :param coluna_cnpj_unidade: Objeto iterável contendo CNPJs.
    :param coluna_cnpj: Objeto iterável contendo CNPJs.
    :param coluna_cpf: Objeto iterável contendo CPFs.
    :return: Registro contendo listas com todos os CNPJs e todos os CPFs. Cada CPF é um objeto com o
        próprio CPF e informações adicionais relevantes (confira).
    """
    registro = RegistroDados()
    for index, CPF in enumerate(coluna_cpf):
        if not isinstance(CPF, str):
            continue
        pos_linha = Int(DELTA + index)
        registro.CPF_lista.append(RegistroCPF(CPF, pos_linha))

    for CNPJ in [*coluna_cnpj_unidade, *coluna_cnpj]:
        if not isinstance(CNPJ, str):
            continue
        if not re.split("[\\/-]", CNPJ)[1] == "0001":
            continue
        if CNPJ in registro.CNPJ_lista:
            continue
        registro.CNPJ_lista.append(CNPJ)

    return registro


def celulas_preenchidas(array: Iterable[Any]) -> Int:
    """Pede uma lista de valores de celulas e retorna quantas estão preenchidos.

    :param array: Objeto iterável contendo um conjunto de células de planilha.
    :return: Quantidade de células que estão preenchidas com qualquer valor que seja.
    """

    # celulas vazias são NaN
    def is_nan(n: Any) -> bool:
        if isinstance(n, float):
            return isnan(n)
        return False

    return Int(len([x for x in array if not is_nan(x)]))


def checar_cpfs_cnpjs(
    cpfs: Iterable[Any], cnpjs: Iterable[Any], cnpjs_unidade: Iterable[Any]
) -> None:
    """Checa se existem CPFs e CNPJs.

    :param cpfs: Objeto iterável contendo células da coluna da planilhas que guarda CPFs.
    :param cnpjs: Objeto iterável contendo CNPJs.
    :param cnpjs_unidade: Objeto iterável contendo CNPJs das unidades.
    :raises ValueError: Nenhum CPF ou nenhum CNPJ encontrado.
    """
    cpfs_qtt: Int = celulas_preenchidas(cpfs)
    cnpjs_qtt: Int = celulas_preenchidas(cnpjs)
    cnpjs_unidade_qtt: Int = celulas_preenchidas(cnpjs_unidade)
    if cpfs_qtt == 0 or cnpjs_qtt + cnpjs_unidade_qtt == 0:
        raise ValueError(
            f"Faltam CPFs ou CNPJs. CPFs: {cpfs_qtt}, CNPJs: {cnpjs_qtt+cnpjs_unidade_qtt}".encode().decode()
        )
