import os
from pathlib import Path
import time
import sys
from os.path import basename, join
from tkinter import messagebox
import shutil
import pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service

from planilha import registro_de_dados_relevantes, DELTA, ColunaPlanilha
from acesso import processar_planilha
from local.io import criar_pastas_de_sistema, PastasSistema


# TODO limitar seleção de planilhas a uma pasta espcífica (C:\\PLANILHAS_SISTEMAS)
# TODO checar erro caso cnpj não tenha procuração
# TODO interagir com páginas apenas se carregada (função acima)
# TODO identificar se falta pouco tempo para o ESOCIAL deslogar; se sim, desloga e loga antes de continuar
# TODO trocar time.sleep por uma forma de idetificar se a página carregou completamente

def main() -> None:
    criar_pastas_de_sistema()
    service = Service('C:\chromedriver_win32 (2)')
    driver = Chrome(service=service)
    while True:
        arquivos_excel: list[str] = []
        with os.scandir(PastasSistema.input) as arquivos:
            for arquivo in arquivos:
                if not arquivo.is_file(): continue
                if not Path(arquivo.path).suffix in ('.xlsx', '.xls'): continue
                # arquivo temporário de criado quando a planilha é aberta
                if basename(arquivo.path).startswith("~$"): continue
                arquivos_excel.append(arquivo.path)

        # se não encontrar nenhum arquivo, espere 2 minutos e cheque de novo
        if len(arquivos_excel) == 0:
            time.sleep(120)
            continue

        for caminho_arquivo_excel in arquivos_excel:
            tabela = None
            if Path(caminho_arquivo_excel).suffix == '.xls':
                tabela = pd.read_excel(caminho_arquivo_excel, header=None, engine='xlrd')
            else:
                tabela = pd.read_excel(caminho_arquivo_excel, header=None, engine='openpyxl')
            
            coluna_cnpj_unidade = tabela.iloc[DELTA:, ColunaPlanilha.CNPJ_UNIDADE].values
            coluna_cnpj = tabela.iloc[DELTA:, ColunaPlanilha.CNPJ].values
            coluna_cpf = tabela.iloc[DELTA:, ColunaPlanilha.CPF].values

            if len(coluna_cnpj_unidade) != len(coluna_cpf):
                raise ValueError(f"Não há a 1 cnpj para cada cpf, {len(coluna_cnpj_unidade)} cnpjs para {len(coluna_cpf)} cpfs.")

            # funcionarios = filtrar_cpfs_apenas_matriz(coluna_cnpj_unidade, coluna_cpf)
            funcionarios = registro_de_dados_relevantes(coluna_cnpj_unidade, coluna_cnpj, coluna_cpf)

            nova_tabela = processar_planilha(driver, funcionarios, tabela)
            while True:
                try:
                    nova_tabela.to_excel(join(PastasSistema.output, basename(caminho_arquivo_excel)),
                                        index=False, header=False, engine='openpyxl')
                    shutil.move(src=caminho_arquivo_excel,
                                dst=join(PastasSistema.pronto, basename(caminho_arquivo_excel)))
                    break
                except PermissionError:
                    mensagem_popup = messagebox.askretrycancel(
                        "Permissão negada!",
                        "Não foi possível salvar o arquivo, pois, o programa não tem permissões o suficiente. Isso também ocorre quando o arquivo já esta aberto em outro programa no momento do salvamento. Feche-o e tente novamente, ou clique em CANCELAR para abortar a execução do programa.")
                    # se o usuario clicar em REPETIR
                    if mensagem_popup: continue
                    else: sys.exit(1)


if __name__ == '__main__':
    main()
    


    