import time
from selenium.webdriver import Chrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import pandas as pd

from erros import FuncionarioNaoEncontradoError
from planilha import RegistroDados, ColunaPlanilha
from local.selenium import *

LINK_PRINCIPAL = 'https://sso.acesso.gov.br/login?client_id=login.esocial.gov.br&authorization_id=188b4b3efd4'
LINK_CNPJ_INPUT = 'https://www.esocial.gov.br/portal/Home/Index?trocarPerfil=true'

def ocorreu_erro_funcionario(driver: Chrome) -> bool:
    mensagem_de_erro = 'Não foi encontrado empregado com o CPF informado.'
    try:
        WebDriverWait(driver, 3).until(ec.all_of(
            ec.presence_of_element_located(Caminhos.ERRO_FUNCIONARIO),
            ec.text_to_be_present_in_element_value(Caminhos.ERRO_FUNCIONARIO, mensagem_de_erro)
        ))
    except TimeoutException: return False
    else: return True

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

def entrar_com_cpf(driver: Chrome, CPF: str) -> None:
    escrever(driver, Caminhos.ESOCIAL_CPF_EMPREGADO_INPUT, Keys.CONTROL+'a', Keys.DELETE)
    escrever(driver, Caminhos.ESOCIAL_CPF_EMPREGADO_INPUT, CPF)
    if ocorreu_erro_funcionario(driver):
        raise FuncionarioNaoEncontradoError()
    apertar_teclas(driver, Keys.ENTER)

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
            time.sleep(20) # hard anti-ddos para evitar deslogar automaticamente

        deslogar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_DESLOGAR)
        deslogar_button.click()
        time.sleep(5)
        driver.get(LINK_CNPJ_INPUT)

    return tabela