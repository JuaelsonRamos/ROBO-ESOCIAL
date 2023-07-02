from collections import namedtuple
import os

PastasSistema = namedtuple("PastasSistema", ['input', 'output', 'pronto', 'nao_excel'])\
    ('C:\\SISTEMA_PLANILHAS', 'C:\\SISTEMA_PLANILHAS_PROCESSADAS',
     'C:\\SISTEMA_PLANILHAS_ARQUIVADAS', 'C:\\SISTEMA_LIXEIRA')

def criar_pastas_de_sistema() -> None:
    for pasta in PastasSistema:
        try:
            os.mkdir(pasta)
        except FileExistsError: pass