import os
from pathlib import Path
import time
import sys
from os.path import basename, join, isdir
from tkinter import messagebox
import shutil
import pandas as pd
from undetected_chromedriver import Chrome
from selenium.webdriver.chrome.service import Service

from planilha import registro_de_dados_relevantes, DELTA, ColunaPlanilha, checar_cpfs_cnpjs
from acesso import processar_planilha
from local.io import criar_pastas_de_sistema, PastasSistema


def main() -> None:
    criar_pastas_de_sistema()
    while True:
        arquivos_excel: list[str] = []
        arquivos_nao_excel: list[str] = []
        with os.scandir(PastasSistema.input) as arquivos:
            for arquivo in arquivos:
                if arquivo.is_dir() or (not Path(arquivo.path).suffix in ('.xlsx', '.xls')):
                    arquivos_nao_excel.append(arquivo.path)
                    continue
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

            checar_cpfs_cnpjs(coluna_cpf, coluna_cnpj, coluna_cnpj_unidade)

            funcionarios = registro_de_dados_relevantes(coluna_cnpj_unidade, coluna_cnpj, coluna_cpf)

            nova_tabela = processar_planilha(funcionarios, tabela)
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
                except FileNotFoundError:
                    break

            pular: bool = False
            for caminho in arquivos_nao_excel:
                while True:
                    try:
                        if isdir(caminho):
                            shutil.move(src=caminho, dst=PastasSistema.nao_excel)
                        else:
                            shutil.move(src=caminho, dst=join(PastasSistema.nao_excel, basename(caminho)))
                        break
                    except PermissionError:
                        mensagem_popup = messagebox.askyesnocancel(
                            "Tentando mover arquivo irrelevante!",
                            f"Arquivo Excel salvo! Porém, arquivos e pastas irrelevantes foram encontradas em {PastasSistema.input} e um ERRO ocorreu ao tentar movê-los, pois, {caminho} está aberto em outro programa. Clique SIM para pular a moção dos arquivos restantes; NÃO para tentar mover novamente o arquivo citado; e CANCELAR para abortar a execução do programa.")
                        if mensagem_popup is None:
                            sys.exit(1)
                        elif mensagem_popup:
                            pular = True
                            break
                        else:
                            continue
                    except FileNotFoundError:
                        break
                if pular: break

if __name__ == '__main__':
    main()
    


    