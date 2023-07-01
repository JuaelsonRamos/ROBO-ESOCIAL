from collections import namedtuple
import os

PastasSistema = namedtuple("PastasSistema", ['input', 'output', 'pronto'])\
    ('C:\\SISTEMA_PLANILHAS', 'C:\\SISTEMA_PLANILHAS_PROCESSADAS', 'C:\\SISTEMA_PLANILHAS_ARQUIVADAS')

def criar_pastas_de_sistema() -> None:
    for pasta in PastasSistema:
        try:
            os.mkdir(pasta)
        except FileExistsError: pass