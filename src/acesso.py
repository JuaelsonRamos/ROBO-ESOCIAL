from undetected_chromedriver import Chrome
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import pandas as pd

from src.erros import FuncionarioNaoEncontradoError
from src.planilha import RegistroDados, ColunaPlanilha, RegistroCPF
from src.utils.selenium import *
from src.utils.acesso import *
from src.caminhos import Caminhos, DadoNaoEncontrado, FuncionarioCrawlerBase
from src.tipos import CelulaVazia

LINK_PRINCIPAL = 'https://sso.acesso.gov.br/login?client_id=login.esocial.gov.br&authorization_id=188b4b3efd4'
LINK_CNPJ_INPUT = 'https://www.esocial.gov.br/portal/Home/Index?trocarPerfil=true'


def carregar_pagina_ate_acessar_perfil(driver: Chrome) -> None:
    driver.get(LINK_PRINCIPAL)
    clicar(driver, Caminhos.ESocial.BOTAO_LOGIN)
    clicar(driver, Caminhos.Govbr.SELECIONAR_CERTIFICADO)
    clicar(driver, Caminhos.ESocial.TROCAR_PERFIL)

def acessar_perfil(driver: Chrome, CNPJ: str) -> None:
    clicar(driver, Caminhos.ESocial.ACESSAR_PERFIL)
    apertar_teclas(driver, Keys.DOWN, Keys.DOWN, Keys.ENTER)

    escrever(driver, Caminhos.ESocial.CNPJ_INPUT, CNPJ)
    
    clicar(driver, Caminhos.ESocial.CNPJ_INPUT_CONFIRMAR)
    clicar(driver, Caminhos.ESocial.CNPJ_SELECIONAR_MODULO)
    clicar(driver, Caminhos.ESocial.MENU_TRABALHADOR)
    clicar(driver, Caminhos.ESocial.MENU_OPCAO_EMPREGADOS)

def entrar_com_cpf(driver: Chrome, CPF: str) -> None:
    escrever(driver, Caminhos.ESocial.CPF_EMPREGADO_INPUT, Keys.CONTROL+'a', Keys.DELETE)
    escrever(driver, Caminhos.ESocial.CPF_EMPREGADO_INPUT, CPF)
    if ocorreu_erro_funcionario(driver):
        raise FuncionarioNaoEncontradoError()
    apertar_teclas(driver, Keys.ENTER)

def raspar_dados(tabela: pd.DataFrame, registro: RegistroCPF, crawler: FuncionarioCrawlerBase) -> None:
    tabela[ColunaPlanilha.SITUACAO][registro.linha] = crawler.SITUACAO
    tabela[ColunaPlanilha.ADMISSAO][registro.linha] = crawler.ADMISSAO
    tabela[ColunaPlanilha.NASCIMENTO][registro.linha] = crawler.NASCIMENTO
    tabela[ColunaPlanilha.MATRICULA][registro.linha] = crawler.MATRICULA

    demissao = CelulaVazia
    try:
        demissao = crawler.DEMISSAO
    except DadoNaoEncontrado:
        pass
    # se o funcionario ainda estiver contratado o campo de demissao não existirá    
    tabela[ColunaPlanilha.DEMISSAO][registro.linha] = demissao

def processar_planilha(funcionarios: RegistroDados, tabela: pd.DataFrame) -> pd.DataFrame:
    apenas_digitos = lambda texto: ''.join([s for s in texto if s in '0123456789'])
    cnpj_index: int = 0
    cpf_index: int = 0
    logout_timeout: float = 10.0
    while True: # emulando um GOTO da vida
        try:
            driver = inicializar_driver()
            carregar_pagina_ate_acessar_perfil(driver)
            teste_deslogado(driver, logout_timeout)

            for i in range(cnpj_index, len(funcionarios.CNPJ_lista)):
                cnpj_index = i
                CNPJ = apenas_digitos(funcionarios.CNPJ_lista[i])

                if i > 0:
                    driver.quit()
                    driver = inicializar_driver()
                    carregar_pagina_ate_acessar_perfil(driver)
                    teste_deslogado(driver, logout_timeout)

                acessar_perfil(driver, CNPJ)
                teste_deslogado(driver, logout_timeout)

                if Caminhos.ESocial.Lista.testar(driver):
                    crawler = Caminhos.ESocial.Lista(driver)
                    for cpf in crawler.proximo_funcionario():
                        for registro in filter(lambda r: r.CPF == cpf, funcionarios.CPF_lista):
                            raspar_dados(tabela, registro, crawler)
                    continue

                # else: assumir formulário
                for j in range(cpf_index, len(funcionarios.CPF_lista)):
                    cpf_index = j
                    registro = funcionarios.CPF_lista[j]
                    CPF = apenas_digitos(registro.CPF)

                    try:
                        entrar_com_cpf(driver, CPF)
                        teste_deslogado(driver, logout_timeout)
                    except FuncionarioNaoEncontradoError:
                        tabela[ColunaPlanilha.MATRICULA][registro.linha] = 'OFF'
                        continue

                    crawler = Caminhos.ESocial.Formulario(driver)
                    raspar_dados(tabela, registro, crawler)
        except (ESocialDeslogadoError, TimeoutException):
            # Capturando TimeoutException para caso a pagina carregue tanto que
            # exceda o tempo de espera para as operações de clicar, escrever, etc.
            # Ou seja, se a pagina carregar de forma incompleta ou nem carregar, ele
            # reinicia o processo de onde parou até conseguir.
            driver.quit()
            continue
        else:
            driver.quit()
            break

    return tabela