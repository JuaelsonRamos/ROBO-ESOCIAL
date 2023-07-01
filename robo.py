import os
import re
import shutil
import sys
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, ElementNotSelectableException, ElementNotVisibleException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from dataclasses import dataclass, field
from collections import namedtuple
from pathlib import Path
from os.path import basename, join
import pyautogui
import time
import pandas as pd
from tkinter import messagebox
from string import ascii_letters

LINK_PRINCIPAL = 'https://sso.acesso.gov.br/login?client_id=login.esocial.gov.br&authorization_id=188b4b3efd4'
LINK_CNPJ_INPUT = 'https://www.esocial.gov.br/portal/Home/Index?trocarPerfil=true'
DELTA = 2

# TODO limitar seleção de planilhas a uma pasta espcífica (C:\\PLANILHAS_SISTEMAS)
# TODO checar erro caso cnpj não tenha procuração

class FuncionarioNaoEncontradoError(Exception): pass

@dataclass(init=False, frozen=True)
class Caminhos:
    ESOCIAL_BOTAO_LOGIN: str = '//*[@id="login-acoes"]/div[2]/p/button'
    SELECIONAR_CERTIFICADO: str = '//*[@id="cert-digital"]/button'
    ESOCIAL_TROCAR_PERFIL: str = '//*[@id="header"]/div[2]/a'
    ESOCIAL_ACESSAR_PERFIL: str = '//*[@id="perfilAcesso"]'
    ESOCIAL_CNPJ_INPUT: str = '//*[@id="procuradorCnpj"]'
    ESOCIAL_CNPJ_INPUT_CONFIRMAR: str = '//*[@id="btn-verificar-procuracao-cnpj"]'
    ESOCIAL_CNPJ_SELECIONAR_MODULO: str = '/html/body/div[3]/div[4]/div/form/div/section/div[7]/div[2]/div[6]'
    ESOCIAL_MENU_TRABALHADOR: str = '//html/body/div[1]/div[2]/div[1]/nav/button'
    ESOCIAL_MENU_OPCAO_EMPREGADOS: str = '/html/body/div[1]/div[2]/div[1]/nav/div/ul/li[1]/a'
    ESOCIAL_CPF_EMPREGADO_INPUT: str = '/html/body/div[1]/div[2]/div[1]/div/div/div/div/div/div/div/div/input'
    ESOCIAL_DESLOGAR: str = '/html/body/div[1]/div[2]/header/div[2]/div[2]/span/a'
    # botão de deslogar está localizado em um lugar diferente se vc partir da tela de login com cnpj
    ESOCIAL_DESLOGAR_CNPJ_INPUT: str = '/html/body/div[3]/div[1]/div[3]'

    # Raspagem de dados
    DADOS_SITUACAO: str = '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[1]/div/p'
    DADOS_NASCIMENTO: str = '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[8]/div/p'
    DADOS_DESLIGAMENTO: str = '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[8]/div/p'
    DADOS_ADMISSAO: str = '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[7]/div/p'
    DADOS_MATRICULA: str = '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[2]/div/p'

    ERRO_FUNCIONARIO: str = '/html/body/div[1]/div[2]/div[1]/div/div[1]/div/div[2]'

def letra_para_numero_coluna(char: str) -> int:
    """Retorna o número correspondente a uma lista de letras em formato de index para o pandas.
    Exemplo: 'L' == 12, portanto esta função retorna 11 (12-1)."""
    num: int = 0
    for c in char:
        if c in ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
    return num - 1

@dataclass(init=False, frozen=True)
class ColunaPlanilha:
    SITUACAO: int = letra_para_numero_coluna('L')
    NASCIMENTO: int = letra_para_numero_coluna('J')
    DESLIGAMENTO: int = letra_para_numero_coluna('N')
    MATRICULA: int = letra_para_numero_coluna('G')
    ADMISSAO: int = letra_para_numero_coluna('M')
    CPF: int = letra_para_numero_coluna('T')
    CNPJ_UNIDADE: int = letra_para_numero_coluna('AM')
    CNPJ: int = letra_para_numero_coluna('BC')

def clicar(driver: Chrome, elemento: str) -> None:
    WebDriverWait(driver, 500).until(
        expected_conditions.element_to_be_clickable((By.XPATH, elemento)))
    driver.find_element(By.XPATH, elemento).click()

def escrever(driver: Chrome, elemento: str, *teclas) -> None:
    WebDriverWait(driver, 500).until(
        expected_conditions.element_to_be_clickable((By.XPATH, elemento)))
    driver.find_element(By.XPATH, elemento).send_keys(*teclas)

def esperar_estar_presente(driver: Chrome, elemento: str) -> None:
    WebDriverWait(driver, 500).until(
        expected_conditions.presence_of_element_located((By.XPATH, elemento)))


def pegar_text(driver: Chrome, caminho: str) -> str:
    esperar_estar_presente(driver, caminho)
    return driver.find_element(By.XPATH, caminho).text

def apertar_teclas(driver: Chrome, *teclas) -> None:
    for tecla in teclas:
        time.sleep(0.300)
        ActionChains(driver).send_keys(tecla).perform()

def esperar_carregar(driver: Chrome) -> None:
    WebDriverWait(driver, 300).until(
        expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, '*')))

# TODO interagir com páginas apenas se carregada (função acima)
# TODO identificar se falta pouco tempo para o ESOCIAL deslogar; se sim, desloga e loga antes de continuar

def carregar_pagina_ate_acessar_perfil(driver: Chrome) -> None:
    driver.get(LINK_PRINCIPAL)
    # TODO deslogar do ESOCIAL antes de carregar a próxima planilha
    clicar(driver, Caminhos.ESOCIAL_BOTAO_LOGIN)
    clicar(driver, Caminhos.SELECIONAR_CERTIFICADO)
    clicar(driver, Caminhos.ESOCIAL_TROCAR_PERFIL)

def acessar_perfil(driver: Chrome, CNPJ: str) -> None:
    clicar(driver, Caminhos.ESOCIAL_ACESSAR_PERFIL)
    apertar_teclas(driver, Keys.DOWN, Keys.DOWN, Keys.ENTER)

    escrever(driver, Caminhos.ESOCIAL_CNPJ_INPUT, CNPJ)
    
    clicar(driver, Caminhos.ESOCIAL_CNPJ_INPUT_CONFIRMAR)
    clicar(driver, Caminhos.ESOCIAL_CNPJ_SELECIONAR_MODULO)
    clicar(driver, Caminhos.ESOCIAL_MENU_TRABALHADOR)
    clicar(driver, Caminhos.ESOCIAL_MENU_OPCAO_EMPREGADOS)

def ocorreu_erro_funcionario(driver: Chrome) -> bool:
    mensagem_de_erro = 'Não foi encontrado empregado com o CPF informado.'
    try:
        WebDriverWait(driver, 3).until(expected_conditions.all_of(
            expected_conditions.presence_of_element_located((By.XPATH, Caminhos.ERRO_FUNCIONARIO)),
            expected_conditions.text_to_be_present_in_element_value((By.XPATH, Caminhos.ERRO_FUNCIONARIO), mensagem_de_erro)
        ))
    except TimeoutException: return False
    else: return True

def entrar_com_cpf(driver: Chrome, CPF: str) -> None:
    escrever(driver, Caminhos.ESOCIAL_CPF_EMPREGADO_INPUT, Keys.CONTROL+'a', Keys.DELETE)
    escrever(driver, Caminhos.ESOCIAL_CPF_EMPREGADO_INPUT, CPF)
    if ocorreu_erro_funcionario(driver):
        raise FuncionarioNaoEncontradoError()
    apertar_teclas(driver, Keys.ENTER)

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
        if not re.split('[\\/-]', CNPJ)[1] == '0001': continue
        if not CNPJ in CATALOGO_FUNCIONARIOS:
            CATALOGO_FUNCIONARIOS[CNPJ] = [RegistroCPF(CPF=CPF, linha=pos_linha)]
        else:
            CATALOGO_FUNCIONARIOS[CNPJ].append(RegistroCPF(CPF=CPF, linha=pos_linha))
    
    return CATALOGO_FUNCIONARIOS

def registro_de_dados_relevantes(coluna_cnpj_unidade, coluna_cnpj, coluna_cpf) -> RegistroDados:
    """Cria um registro de todos os cpnjs da MATRIZ e TODOS os cpfs."""
    registro = RegistroDados()
    for index, CPF in enumerate(coluna_cpf):
        pos_linha = DELTA + index
        registro.CPF_lista.append(RegistroCPF(CPF, pos_linha))

    for CNPJ in [*coluna_cnpj_unidade, *coluna_cnpj]:
        if not isinstance(CNPJ, str): continue
        if not re.split('[\\/-]', CNPJ)[1] == '0001': continue
        if CNPJ in registro.CNPJ_lista: continue
        registro.CNPJ_lista.append(CNPJ)

    return registro

def processar_planilha(driver: Chrome, funcionarios: RegistroDados, tabela: pd.DataFrame) -> pd.DataFrame:
    apenas_digitos = lambda texto: ''.join([s for s in texto if s in '0123456789'])
    carregar_pagina_ate_acessar_perfil(driver)
    for CNPJ in funcionarios.CNPJ_lista:
        CNPJ = apenas_digitos(CNPJ)

        acessar_perfil(driver, CNPJ)

        for registro in funcionarios.CPF_lista:
            CPF = apenas_digitos(registro.CPF)

            try:
                entrar_com_cpf(driver, CPF)
            except FuncionarioNaoEncontradoError:
                tabela[ColunaPlanilha.MATRICULA][registro.linha] = 'OFF'
                continue

            tabela[ColunaPlanilha.SITUACAO][registro.linha] = pegar_text(driver, Caminhos.DADOS_SITUACAO)
            tabela[ColunaPlanilha.ADMISSAO][registro.linha] = pegar_text(driver, Caminhos.DADOS_ADMISSAO)
            tabela[ColunaPlanilha.NASCIMENTO][registro.linha] = pegar_text(driver, Caminhos.DADOS_NASCIMENTO)
            tabela[ColunaPlanilha.MATRICULA][registro.linha] = str(pegar_text(driver, Caminhos.DADOS_MATRICULA))
            tabela[ColunaPlanilha.DESLIGAMENTO][registro.linha] = pegar_text(driver, Caminhos.DADOS_DESLIGAMENTO)

        deslogar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_DESLOGAR)
        deslogar_button.click()
        time.sleep(5)
        driver.get(LINK_CNPJ_INPUT)

    return tabela
            
PastasSistema = namedtuple("PastasSistema", ['input', 'output', 'pronto'])\
    ('C:\\SISTEMA_PLANILHAS', 'C:\\SISTEMA_PLANILHAS_PROCESSADAS', 'C:\\SISTEMA_PLANILHAS_ARQUIVADAS')

def criar_pastas_de_sistema() -> None:
    for pasta in PastasSistema:
        try:
            os.mkdir(pasta)
        except FileExistsError: pass
   
# TODO trocar time.sleep por uma forma de idetificar se a página carregou completamente

def main() -> None:
    criar_pastas_de_sistema()
    service = Service('C:\chromedriver_win32 (2)')
    driver = webdriver.Chrome(service=service)
    while True:
        # try:
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
                    # shutil.move(src=caminho_arquivo_excel,
                    #             dst=join(PastasSistema.pronto, basename(caminho_arquivo_excel)))
                    break
                except PermissionError:
                    mensagem_popup = messagebox.askretrycancel(
                        "Permissão negada!",
                        "Não foi possível salvar o arquivo, pois, o programa não tem permissões o suficiente. Isso também ocorre quando o arquivo já esta aberto em outro programa no momento do salvamento. Feche-o e tente novamente, ou clique em CANCELAR para abortar a execução do programa.")
                    # se o usuario clicar em REPETIR
                    if mensagem_popup: continue
                    else: sys.exit(1)
        # except (NoSuchElementException, ElementNotVisibleException,
        #         ElementNotInteractableException, ElementNotSelectableException):
        #     driver.quit()
        #     continue


if __name__ == '__main__':
    main()
    


    