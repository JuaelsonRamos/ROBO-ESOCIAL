from dataclasses import dataclass, field
from string import ascii_letters
from math import isnan
import re

DELTA: int = 2


def letra_para_numero_coluna(char: str) -> int:
    """Retorna o número correspondente a uma lista de letras em formato de index para o pandas.
    Exemplo: 'L' == 12, portanto esta função retorna 11 (12-1)."""
    num: int = 0
    for c in char:
        if c in ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord("A")) + 1
    return num - 1


@dataclass(init=False, frozen=True)
class ColunaPlanilha:
    SITUACAO: int = letra_para_numero_coluna("L")
    NASCIMENTO: int = letra_para_numero_coluna("J")
    DEMISSAO: int = letra_para_numero_coluna("N")
    MATRICULA: int = letra_para_numero_coluna("G")
    ADMISSAO: int = letra_para_numero_coluna("M")
    CPF: int = letra_para_numero_coluna("T")
    CNPJ_UNIDADE: int = letra_para_numero_coluna("AM")
    CNPJ: int = letra_para_numero_coluna("BC")


# catalogando cpf para cada cnpj
@dataclass(init=True, frozen=True)
class RegistroCPF:
    # cpf com pontuação
    CPF: str
    linha: int


@dataclass(init=True, frozen=True)
class RegistroDados:
    CNPJ_lista: list[str] = field(init=False, default_factory=list)
    CPF_lista: list[RegistroCPF] = field(init=False, default_factory=list)


# ESSA FUNÇÃO NÃO ESTÁ MAIS SENDO USADA; MANTIDA AQUI CASO MUDE DE IDEA
def filtrar_cpfs_apenas_matriz(coluna_cnpj, coluna_cpf) -> dict[str, list[RegistroCPF]]:
    """Cria um dicionário apenas com os cnpjs da matriz e os cpfs correspondentes
    a esses cpnjs."""
    CATALOGO_FUNCIONARIOS: dict[str, list[RegistroCPF]] = {}
    for index, info in enumerate(zip(coluna_cnpj, coluna_cpf)):
        pos_linha = DELTA + index
        CNPJ, CPF = info
        if not re.split("[\\/-]", CNPJ)[1] == "0001":
            continue
        if not CNPJ in CATALOGO_FUNCIONARIOS:
            CATALOGO_FUNCIONARIOS[CNPJ] = [RegistroCPF(CPF=CPF, linha=pos_linha)]
        else:
            CATALOGO_FUNCIONARIOS[CNPJ].append(RegistroCPF(CPF=CPF, linha=pos_linha))

    return CATALOGO_FUNCIONARIOS


def registro_de_dados_relevantes(coluna_cnpj_unidade, coluna_cnpj, coluna_cpf) -> RegistroDados:
    """Cria um registro de todos os cpnjs da MATRIZ e TODOS os cpfs."""
    registro = RegistroDados()
    for index, CPF in enumerate(coluna_cpf):
        if not isinstance(CPF, str):
            continue
        pos_linha = DELTA + index
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


def celulas_preenchidas(array) -> int:
    """Pede uma lista de valores de celulas e retorna quantas estão preenchidos."""
    # celulas vazias são NaN
    return len(list(filter(lambda x: (not isnan(x) if isinstance(x, float) else True), array)))


def checar_cpfs_cnpjs(cpfs, cnpjs, cnpjs_unidade) -> None:
    cpfs_qtt: int = celulas_preenchidas(cpfs)
    cnpjs_qtt: int = celulas_preenchidas(cnpjs)
    cnpjs_unidade_qtt: int = celulas_preenchidas(cnpjs_unidade)
    if cpfs_qtt == 0 or cnpjs_qtt + cnpjs_unidade_qtt == 0:
        raise ValueError(
            f"Faltam CPFs ou CNPJs. CPFs: {cpfs_qtt}, CNPJs: {cnpjs_qtt+cnpjs_unidade_qtt}".encode()
        )
