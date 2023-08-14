""" Operações relacionadas ao acesso das páginas web e processamento de planilhas que tem a ver com
essas páginas."""

from typing import Optional
import pandas as pd
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from undetected_chromedriver import Chrome
from string import digits

from src.webdriver.caminhos import Caminhos, DadoNaoEncontrado, FuncionarioCrawlerBase
from src.webdriver.erros import FuncionarioNaoEncontradoError
from src.webdriver.planilha import ColunaPlanilha, RegistroCPF, RegistroDados
from src.webdriver.tipos import CelulaVazia, Int
from src.webdriver.utils.acesso import ocorreu_erro_funcionario, inicializar_driver, teste_deslogado
from src.webdriver.utils.selenium import clicar, apertar_teclas, escrever
from src.webdriver.erros import ESocialDeslogadoError

__all__ = [
    "LINK_CNPJ_INPUT",
    "LINK_PRINCIPAL",
    "acessar_perfil",
    "carregar_pagina_ate_acessar_perfil",
    "entrar_com_cpf",
    "processar_planilha",
    "raspar_dados",
]

LINK_PRINCIPAL = "https://login.esocial.gov.br/login.aspx"
LINK_CNPJ_INPUT = "https://www.esocial.gov.br/portal/Home/Index?trocarPerfil=true"


def carregar_pagina_ate_acessar_perfil(driver: Chrome) -> None:
    """Interage com os elementos corretos até chegar na página de acesso perfil com base no CNPJ.

    :param driver: Webdriver ativo na hora do acesso.
    """
    driver.get(LINK_PRINCIPAL)
    clicar(driver, Caminhos.ESocial.BOTAO_LOGIN)
    clicar(driver, Caminhos.Govbr.SELECIONAR_CERTIFICADO)
    clicar(driver, Caminhos.ESocial.TROCAR_PERFIL)


def acessar_perfil(driver: Chrome, CNPJ: str) -> None:
    """Interage com os elementos corretos para entrar com os dados e acessar o perfil da empresa com
    base no CNPJ.

    :param driver: Webdriver ativo na hora do acesso.
    :param CNPJ: CNPJ da empresa cujo perfil deve ser acessado.
    """
    clicar(driver, Caminhos.ESocial.ACESSAR_PERFIL)
    apertar_teclas(driver, Keys.DOWN, Keys.DOWN, Keys.ENTER)

    escrever(driver, Caminhos.ESocial.CNPJ_INPUT, CNPJ)

    clicar(driver, Caminhos.ESocial.CNPJ_INPUT_CONFIRMAR)
    clicar(driver, Caminhos.ESocial.CNPJ_SELECIONAR_MODULO)
    clicar(driver, Caminhos.ESocial.MENU_TRABALHADOR)
    clicar(driver, Caminhos.ESocial.MENU_OPCAO_EMPREGADOS)


def entrar_com_cpf(driver: Chrome, CPF: str) -> None:
    """Entra com os dados do CPF do funcionário quando a forma de pesquisa de funcionários é o
    formulário.

    :param driver: Webdriver ativo na hora do acesso.
    :param CPF: CPF do funcionário com ou sem pontuação.
    """
    escrever(driver, Caminhos.ESocial.CPF_EMPREGADO_INPUT, Keys.CONTROL + "a", Keys.DELETE)
    escrever(driver, Caminhos.ESocial.CPF_EMPREGADO_INPUT, CPF)
    if ocorreu_erro_funcionario(driver):
        raise FuncionarioNaoEncontradoError()
    apertar_teclas(driver, Keys.ENTER)


def raspar_dados(
    tabela: pd.DataFrame, registro: RegistroCPF, crawler: FuncionarioCrawlerBase
) -> None:
    """Pega os dados do funcionário utilizando a instância do crawler especificado e posiciona os
    dados encontrados na tabela utilizando a posição do CPF relativo a posição dos dados raspados na
    planilha.

    :param tabela: Dataframe que representa a planilha que será mudada.
    :param registro: Dados do CPF (como posição dele na planilha).
    :param crawler: Instância do crawler correto para raspar os dados do funcionário na página.
    :raises DadoNaoEncontrado: Quando o dado que você está tentando acessar não existe na pagina.
    """
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
    """Inicializa o webdriver, acessa a página de raspagem e raspa os dados.

    :param funcionarios: Registro de CPNJs e CPFs.
    :param tabela: Representação da planilha.
    :return: Nova planilha com dados mudados.
    """

    def apenas_digitos(texto: str) -> str:
        """Remove todos os caracteres que não sao números de um texto."""
        return "".join([s for s in texto if s in digits])

    cnpj_index = Int(0)
    cpf_index = Int(0)
    logout_timeout = Int(10)
    while True:  # emulando um GOTO da vida
        driver: Optional[Chrome] = None
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
                        generator = (r for r in funcionarios.CPF_lista if r.CPF == cpf)
                        for registro in generator:
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
                        tabela[ColunaPlanilha.MATRICULA][registro.linha] = "OFF"
                        continue

                    crawler = Caminhos.ESocial.Formulario(driver)
                    raspar_dados(tabela, registro, crawler)
        except (ESocialDeslogadoError, TimeoutException):
            # Capturando TimeoutException para caso a pagina carregue tanto que
            # exceda o tempo de espera para as operações de clicar, escrever, etc.
            # Ou seja, se a pagina carregar de forma incompleta ou nem carregar, ele
            # reinicia o processo de onde parou até conseguir.
            if driver:
                driver.quit()
            continue
        else:
            driver.quit()
            break

    return tabela
