import time

from typing import Optional, Set
import pandas as pd

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from string import digits

from src.webdriver.caminhos import Caminhos, DadoNaoEncontrado, FuncionarioCrawlerBase
from src.webdriver.erros import FuncionarioNaoEncontradoError
from src.webdriver.planilha import ColunaPlanilha, RegistroCPF, RegistroDados
from src.webdriver.types import CelulaVazia
from src.local.types import Int
from src.utils.acesso import (
    botao_funcionario,
    ocorreu_erro_funcionario,
    inicializar_driver,
    teste_deslogado,
)
from src.utils.selenium import clicar, apertar_teclas, escrever
from src.webdriver.erros import ESocialDeslogadoError
from src.utils.python import LoopState
from src.async_vitals.messaging import ProgressStateNamespace as progress_values


__all__ = [
    "LINK_CNPJ_INPUT",
    "LINK_PRINCIPAL",
    "acessar_perfil",
    "carregar_pagina_ate_acessar_perfil",
    "carregar_pagina_ate_cpf_input",
    "entrar_com_cpf",
    "processar_planilha",
    "raspar_dados",
]


LINK_PRINCIPAL = "https://login.esocial.gov.br/login.aspx"
LINK_CNPJ_INPUT = "https://www.esocial.gov.br/portal/Home/Index?trocarPerfil=true"
logout_timeout = Int(10)


def carregar_pagina_ate_acessar_perfil(driver: uc.Chrome) -> None:
    """Interage com os elementos corretos até chegar na página de acesso perfil.

    :param driver: Webdriver ativo na hora do acesso.
    """
    driver.get(LINK_PRINCIPAL)
    # Pausa para resolução manual do CAPTCHA
    print("\n⚠️ Por favor, resolva o CAPTCHA no navegador e pressione Enter aqui para continuar...")
    input()
    clicar(driver, Caminhos.ESocial.BOTAO_LOGIN)
    clicar(driver, Caminhos.Govbr.SELECIONAR_CERTIFICADO)
    clicar(driver, Caminhos.ESocial.TROCAR_PERFIL)


def acessar_perfil(driver: uc.Chrome, CNPJ: str) -> None:
    """Interage com os elementos corretos para entrar com os dados e acessar o
    base no CNPJ.

    :param driver: Webdriver ativo na hora do acesso.
    :param CNPJ: CNPJ da empresa cujo perfil deve ser acessado.
    """
    escrever(driver, Caminhos.ESocial.CNPJ_INPUT, CNPJ)
    clicar(driver, Caminhos.ESocial.CNPJ_INPUT_CONFIRMAR)
    clicar(driver, Caminhos.ESocial.CNPJ_SELECIONAR_MODULO)
    clicar(driver, Caminhos.ESocial.MENU_TRABALHADOR)
    clicar(driver, Caminhos.ESocial.MENU_OPCAO_EMPREGADOS)


def entrar_com_cpf(driver: uc.Chrome, CPF: str) -> None:
    """Entra com os dados do CPF do funcionário quando a forma de pesquisa de
    formulário.

    :param driver: Webdriver ativo na hora do acesso.
    :param CPF: CPF do funcionário com ou sem pontuação.
    """
    escrever(driver, Caminhos.ESocial.CPF_EMPREGADO_INPUT, Keys.CONTROL + "a", Keys.DELETE)
    escrever(driver, Caminhos.ESocial.CPF_EMPREGADO_INPUT, CPF)
    if ocorreu_erro_funcionario(driver):
        raise FuncionarioNaoEncontradoError()

    if botao := botao_funcionario(driver, CPF):
        botao.click()
    else:
        raise FuncionarioNaoEncontradoError()


def raspar_dados(
    tabela: pd.DataFrame, registro: RegistroCPF, crawler: FuncionarioCrawlerBase
) -> None:
    """Pega os dados do funcionário utilizando a instância do crawler especificada e
    dados encontrados na tabela utilizando a posição do CPF relativo a posição da
    planilha.

    :param tabela: DataFrame que representa a planilha que será mudada.
    :param registro: Dados do CPF (como posição dele na planilha).
    :param crawler: Instância do crawler correto para raspar os dados do funcionário.
    :raises DadoNaoEncontrado: Quando o dado que você está tentando acessar não é encontrado.
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
    # se o funcionario ainda estiver contratado o campo de demissao não existe
    tabela[ColunaPlanilha.DEMISSAO][registro.linha] = demissao


def carregar_pagina_ate_cpf_input(driver: uc.Chrome, CNPJ: str) -> None:
    """Abstração do processo de chegar até o ponto de selecionar os funcionários e
    dados.
    """
    carregar_pagina_ate_acessar_perfil(driver)
    teste_deslogado(driver, logout_timeout)
    acessar_perfil(driver, CNPJ)
    teste_deslogado(driver, logout_timeout)


def processar_planilha(
    funcionarios: RegistroDados, tabela: pd.DataFrame, progress_values: progress_values
) -> pd.DataFrame:
    """Inicializa o webdriver, acessa a página de raspagem e raspa os dados.

    :param funcionarios: Registro de dados dos funcionários.
    :param tabela: Tabela de dados para ser preenchida.
    :param progress_values: Objeto para atualização do progresso.
    :return: Nova planilha com dados mudados.
    """
    progress_values.t.update_general_msg(progress_values, "Iniciando etapa de raspagem de dados...")
    progress_values.cpf_max = len(funcionarios.CPF_lista)
    progress_values.cpf_current = Int(0)
    progress_values.cpf_last_updated_ns = time.time_ns()

    for cpf, nome in funcionarios.CPF_lista:
        with progress_values.get_lock():
            progress_values.cpf_current += 1
            progress_values.cpf_last_updated_ns = time.time_ns()
            progress_values.t.set_string(progress_values.cpf_msg, STR_DUMMY)
            progress_values.cpf_last_updated_ns = time.time_ns()

        if driver:
            # É necessário reiniciar o driver para cada CNPJ
            driver.quit()
        progress_values.t.update_general_msg(
            progress_values, "Inicializando motor de busca e recolhimento"
        )
        driver = inicializar_driver()
        try:
            progress_values.t.update_general_msg(
                progress_values, "Acessando perfil da empresa utilizando o"
            )
            carregar_pagina_ate_cpf_input(driver, cnpj)
        except (ESocialDeslogadoError, TimeoutException):
            # Capturando TimeoutException para caso a pagina carregue tanto
            # que exceda o tempo de espera para as operações de clicar, escrever
            # Ou seja, se a pagina carregar de forma incompleta ou nem carregar
            # reinicia o processo de onde parou até conseguir.
            continue

        if Caminhos.ESocial.Lista.testar(driver):
            progress_values.t.update_general_msg(
                progress_values,
                "Encontrada lista pré-definida de funcionários. Coletando"
            )
            crawler = Caminhos.ESocial.Lista(driver)
            with progress_values.get_lock():
                progress_values.cpf_max = crawler.quantos
                progress_values.cpf_current = Int(0)
                progress_values.cpf_last_updated_ns = time.time_ns()
                progress_values.t.set_string(progress_values.cpf_msg, STR_DUMMY)
                progress_values.cpf_last_updated_ns = time.time_ns()

            for cpf, nome in crawler.proximo_funcionario():
                with progress_values.get_lock():
                    progress_values.cpf_current += 1
                    progress_values.cpf_last_updated_ns = time.time_ns()
                    progress_values.t.set_string(progress_values.cpf_msg, STR_DUMMY)
                    progress_values.cpf_last_updated_ns = time.time_ns()

                generator = (r for r in funcionarios.CPF_lista if r.CPF == cpf)
                for registro in generator:
                    if registro.CPF in cpfs_ja_vistos:
                        continue
                    raspar_dados(tabela, registro, crawler)
                    cpfs_ja_vistos.add(registro.CPF)

            cnpj_loop.unlock()
            with progress_values.get_lock():
                progress_values.cpf_max = len(funcionarios.CPF_lista)
                progress_values.cpf_current = Int(0)
                progress_values.cpf_last_updated_ns = time.time_ns()
                progress_values.t.set_string(progress_values.cpf_msg, STR_DUMMY)
                progress_values.cpf_last_updated_ns = time.time_ns()

        else: # assumir formulário
            cpf_form_loop = LoopState(iter(range(cpf_index, len(funcionarios.CPF_lista))))
            restart: bool = False
            while True:
                if restart:
                    # Só reinicia o driver para o CPF caso um erro ocorra
                    if driver:
                        driver.quit()
                    try:
                        progress_values.t.update_general_msg(
                            progress_values, "Inicializando motor de busca e recolhimento"
                        )
                        driver = inicializar_driver()
                        progress_values.t.update_general_msg(
                            progress_values, "Acessando perfil da empresa utilizando o"
                        )
                        carregar_pagina_ate_cpf_input(driver, cnpj)
                    except (ESocialDeslogadoError, TimeoutException):
                        continue

                if not cpf_form_loop.locked:
                    try:
                        cpf_index = Int(next(cpf_form_loop.iterator()))
                    except StopIteration:
                        break
                    with progress_values.get_lock():
                        progress_values.cpf_current += 1
                        progress_values.cpf_last_updated_ns = time.time_ns()
                    cpf_form_loop.lock()

                cnpj_registro = funcionarios.CNPJ_lista[cnpj_index]
                with progress_values.get_lock():
                    progress_values.cpf_current = cnpj_index
                    progress_values.t.set_string(progress_values.cpf_msg, cnpj_registro.CPF)
                    progress_values.cpf_last_updated_ns = time.time_ns()

                cpf_registro = funcionarios.CPF_lista[cpf_index]
                with progress_values.get_lock():
                    progress_values.cpf_current = cpf_index
                    progress_values.t.set_string(progress_values.cpf_msg, cpf_registro.CPF)
                    progress_values.cpf_last_updated_ns = time.time_ns()

                try:
                    entrar_com_cpf(driver, cpf_registro.CPF)
                    raspar_dados(tabela, cpf_registro, crawler)
                    restart = False
                except (FuncionarioNaoEncontradoError, TimeoutException):
                    restart = True
                    continue

                cpf_form_loop.unlock()

    return tabela


def apenas_digitos(texto: str) -> str:
    """Remove todos os caracteres que não sao números de um texto."""
    return "".join([s for s in texto if s in digits])


STR_DUMMY = "Processando..."

