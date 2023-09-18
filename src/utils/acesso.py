"""Operações úteis e genéricas relacionadas ao acesso das páginas web relevantes ao programa."""

import datetime
import time
from sys import maxsize as MAX_INT
from typing import cast, List

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome
from webdriver_manager.chrome import ChromeDriverManager

import src.webdriver.windows as windows
from src.webdriver.caminhos import Caminhos
from src.webdriver.erros import ESocialDeslogadoError
from src.utils.python import DEBUG
from src.utils.selenium import esperar_estar_presente
from src.local.types import Int, Float

__all__ = [
    "botao_funcionario",
    "deslogado",
    "inicializar_driver",
    "ocorreu_erro_funcionario",
    "segundos_restantes_de_sessao",
    "teste_deslogado",
]


def deslogado(driver: Chrome, timeout: Int) -> bool:
    """Testa se o elemento da mensagem de logout do ESocial aparece dentro do limite de tempo
    especificado.

    :param driver: Webdriver ativo no hora da checagem.
    :param timeout: Tempo para esperar antes de assumir que o perfil não foi deslogado.
    :return: Se o perfil foi deslogado ou não.
    """
    try:
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located(Caminhos.ESocial.LOGOUT)
        )
    except TimeoutException:
        return False
    else:
        return True


def segundos_restantes_de_sessao(driver: Chrome) -> Int:
    """Retorna a quantidade de segundos restantes antes da sessão acabar ou um número absurdamente
    alto se algum erro acontecer.

    :param driver: Webdriver ativo no momento da checagem.
    :return: Número de segundos restantes para a sessão.
    """
    esperar_estar_presente(driver, Caminhos.ESocial.TEMPO_SESSAO)
    tempo: str = driver.find_element(*Caminhos.ESocial.TEMPO_SESSAO).text
    try:
        t: time.struct_time = time.strptime(tempo, "%M:%S")
        return Int(datetime.timedelta(minutes=t.tm_min, seconds=t.tm_sec).total_seconds())
    except ValueError:
        return Int(MAX_INT)


def inicializar_driver() -> Chrome:
    """Inicializa o webdriver com as opções e características necessárias.

    :return: Instância do webdriver.
    """
    driver = Chrome(driver_executable_path=ChromeDriverManager().install())
    driver.set_window_rect(x=0, y=0, width=1280, height=720)
    if not DEBUG:
        windows.bloquear_janela(driver)
    return driver


def teste_deslogado(driver: Chrome, timeout: Int) -> None:
    """Testa se o ESocial for deslogado ao checar o tempo restante de sessão e a mensagem de logout.

    :param driver: Webdriver ativo na hora do teste.
    :param timeout: Tempo limite de espera antes de assumir que a mensagem não existe.
    """
    if segundos_restantes_de_sessao(driver) <= (10 * 60) or deslogado(driver, Int(timeout)):
        raise ESocialDeslogadoError()


def botao_funcionario(driver: Chrome, CPF: str) -> WebElement | None:
    """Seleciona o botão que vai levar para a página de dados do funcionário referente ao CPF
    especificado na seleção por formulário.

    :param driver: Webdriver.
    :param CPF: CPF do funcionário cujos dados devem ser acessados.
    """
    esperar_estar_presente(driver, Caminhos.ESocial.CPF_OPCAO)
    opcoes: List[WebElement] = driver.find_elements(*Caminhos.ESocial.CPF_OPCAO)
    if len(botoes_corretos := [o for o in opcoes if CPF in o.text]) > 0:
        return botoes_corretos[0]
    return None


def ocorreu_erro_funcionario(driver: Chrome) -> bool:
    """Checa se algum erro relacionado ao funcionário ocorreu.

    :param driver: Webdriver ativo na hora da checagem.
    :return: Se o erro ocorreu ou não.
    """

    esperar_estar_presente(driver, Caminhos.ESocial.CPF_EMPREGADO_INPUT)
    element: WebElement = driver.find_element(*Caminhos.ESocial.CPF_EMPREGADO_INPUT)

    try:
        esperar_estar_presente(driver, Caminhos.ESocial.CPF_OPCAO, Float(15))
    except TimeoutException:
        return True

    cpf = cast(str, element.get_attribute("value"))
    if botao_funcionario(driver, cpf):
        return False
    return True
