import time
from undetected_chromedriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import pandas as pd

from erros import FuncionarioNaoEncontradoError, ESocialDeslogadoError
from planilha import RegistroDados, ColunaPlanilha
from local.selenium import *
import windows

LINK_PRINCIPAL = 'https://sso.acesso.gov.br/login?client_id=login.esocial.gov.br&authorization_id=188b4b3efd4'
LINK_CNPJ_INPUT = 'https://www.esocial.gov.br/portal/Home/Index?trocarPerfil=true'

def ocorreu_erro_funcionario(driver: Chrome) -> bool:

    def mensagem_de_erro_existe() -> bool:
        mensagem_de_erro = 'Não foi encontrado empregado com o CPF informado.'
        try:
            WebDriverWait(driver, 3).until(ec.all_of(
                # TODO adicionar todos os métodos de checagem de texto dentro de uma condição OR
                ec.presence_of_element_located(Caminhos.ERRO_FUNCIONARIO),
                ec.text_to_be_present_in_element(Caminhos.ERRO_FUNCIONARIO, mensagem_de_erro)
            ))
        except TimeoutException: return False
        else: return True

    # TODO remover a habilidade do usuário de interagir e mudar o tamanho do navegador, apenas mover a janela
    def resultado_cpf_encontrado() -> bool:
        esperar_estar_presente(driver, Caminhos.ESOCIAL_CPF_EMPREGADO_INPUT)
        element: WebElement = driver.find_element(*Caminhos.ESOCIAL_CPF_EMPREGADO_INPUT)
        id: str = element.get_attribute("aria-controls")
        cpf: str = element.get_attribute("value")
        css_selector: str = f"#{id} > li:nth-child(1)"
        try:
            WebDriverWait(driver, 5).until(ec.all_of(
                ec.presence_of_element_located((By.CSS_SELECTOR, css_selector)),
                ec.text_to_be_present_in_element((By.CSS_SELECTOR, css_selector), cpf)
            ))
        except TimeoutException: return False
        else: return True

    if resultado_cpf_encontrado(): return False
    return True

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

def teste_deslogado(driver: Chrome, timeout: int) -> None:
    if segundos_restantes_de_sessao(driver) <= (10*60) or deslogado(driver, timeout):
        raise ESocialDeslogadoError()

def processar_planilha(funcionarios: RegistroDados, tabela: pd.DataFrame) -> pd.DataFrame:
    apenas_digitos = lambda texto: ''.join([s for s in texto if s in '0123456789'])
    cnpj_index: int = 0
    cpf_index: int = 0
    logout_timeout: float = 10.0
    while True: # emulando um GOTO da vida
        try:
            driver = Chrome()
            driver.set_window_rect(x=0, y=0, width=1280, height=720)
            windows.bloquear_janela(driver) # necessariamente antes de iniciar o acesso
            carregar_pagina_ate_acessar_perfil(driver)
            teste_deslogado(driver, logout_timeout)
            
            for i in range(cnpj_index, len(funcionarios.CNPJ_lista)):
                cnpj_index = i
                CNPJ = apenas_digitos(funcionarios.CNPJ_lista[i])

                acessar_perfil(driver, CNPJ)
                teste_deslogado(driver, logout_timeout)

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

                    tabela[ColunaPlanilha.SITUACAO][registro.linha] = pegar_text(driver, Caminhos.DADOS_SITUACAO)
                    tabela[ColunaPlanilha.ADMISSAO][registro.linha] = pegar_text(driver, Caminhos.DADOS_ADMISSAO)
                    tabela[ColunaPlanilha.NASCIMENTO][registro.linha] = pegar_text(driver, Caminhos.DADOS_NASCIMENTO)
                    tabela[ColunaPlanilha.MATRICULA][registro.linha] = str(pegar_text(driver, Caminhos.DADOS_MATRICULA))
                    tabela[ColunaPlanilha.DESLIGAMENTO][registro.linha] = pegar_text(driver, Caminhos.DADOS_DESLIGAMENTO)
        except (ESocialDeslogadoError, TimeoutException):
            # Capturando TimeoutException para caso a pagina carregue tanto que
            # exceda o tempo de espera para as operações de clicar, escrever, etc.
            # Ou seja, se a pagina carregar de forma incompleta ou nem carregar, ele
            # reinicia o processo de onde parou até conseguir.
            # TODO notificação especial caso o processo reinicie por conta de timeout
            driver.quit()
            continue
        else:
            driver.quit()
            # TODO notificação aqui
            break

    return tabela