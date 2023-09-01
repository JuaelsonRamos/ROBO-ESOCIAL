""" Operações úteis e genérias relacionadas ao Selenium."""

import time
from typing import Callable, Literal
import math
from urllib.parse import urlparse

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from undetected_chromedriver import Chrome

from src.tipos import SeletorHTML, Float
from src.erros import ErroInternoSistema

__all__ = ["ERRO_PERIODO_SECS", "TIMEOUT_SECS", "apertar_teclas", "checar_erros_entre_esperas", "clicar", "escrever", "esperar_estar_presente", "pagina_de_erro", "pegar_text"]

TIMEOUT_SECS = Float(120.0)
""" Segundos para esperar antes de assumir que a página demorou demais para carregar."""
ERRO_PERIODO_SECS  = Float(2.0)
""" Quantidade de segundos para esperar antes de checar por erros."""

def pagina_de_erro(driver: Chrome) -> bool:
    """ Retorna se a página atual é uma página de erro.

    :param driver: Webdriver.
    """
    return urlparse(driver.current_url).path.split("/")[-1].lower() == "erro"

def checar_erros_entre_esperas(driver: Chrome, condition: Callable[[ec.AnyDriver], WebElement | bool], timeout: Float = TIMEOUT_SECS) -> None:
    """ Espera a condição especificada ser cumprida.

    A cada dado intervalo de tempo esta função checa por possíveis erros. Se um erro ocorrer, a
    respectiva Exception é levantada; se não, a função retorna None, significando que a condição foi
    cumprida com sucesso.

    :param driver: Webdriver.
    :param condition: Condição de espera como expecificado por :mod:`selenium.webdriver.support.expected_conditions`.
    :param timeout: Tempo máximo para esperar.
    :raise TimeoutException: Exception padrão caso a condição não seja cumprida dentro do prazo estipulado.
    :raise ErroInternoSistema: Erro genérico do sistema que impede o acesso.
    """
    last_exception: TimeoutException | None = None
    loop_times = 1 if timeout < ERRO_PERIODO_SECS else timeout / ERRO_PERIODO_SECS
    # 'float' sendo 0 < x < 1
    resto: float | None | Literal[0] = loop_times % 1 if loop_times % 1 < 1 else None

    for i in range(math.ceil(loop_times)):
        periodo = ERRO_PERIODO_SECS if timeout >= ERRO_PERIODO_SECS else timeout
        if resto and i + 1 == math.ceil(loop_times):
            # ultimo loop
            periodo = resto
        try:
            WebDriverWait(driver, periodo).until(condition)
        except TimeoutException as err:
            if pagina_de_erro(driver):
                raise ErroInternoSistema() from err
            if i + 1 == math.ceil(loop_times):
                # ultimo loop
                last_exception = err
            continue
        else:
            break
    if last_exception:
        # Se todo o tempo tiver passado e condição não foi cumprida,
        # mas nenhum erro ocorreu.
        raise last_exception


def clicar(driver: Chrome, locator: SeletorHTML) -> None:
    """ Espera o elemento estar disponível e clica nele.

    :param driver: Webdriver ativo no momento do clique.
    :param locator: Seletor que representa o elemento HTML que deve ser clicado.
    """
    checar_erros_entre_esperas(driver, ec.element_to_be_clickable(locator))
    driver.find_element(*locator).click()


def escrever(driver: Chrome, locator: SeletorHTML, *teclas: str) -> None:
    """ Espera o elemento estar disponível e escreve nele.

    :param driver: Webdriver ativo no momento do clique.
    :param locator: Seletor que representa o elemento HTML que deve ser clicado.
    :param teclas: Lista de teclas a serem tecladas.
    """
    checar_erros_entre_esperas(driver, ec.element_to_be_clickable(locator))
    driver.find_element(*locator).send_keys(*teclas)


def esperar_estar_presente(driver: Chrome, locator: SeletorHTML, timeout: Float = TIMEOUT_SECS) -> None:
    """ Espera um elemento HTML estar presente na página.

    :param driver: Webdriver ativo no momento do clique.
    :param locator: Seletor que representa o elemento HTML que deve ser clicado.
    :param timeout: Tempo máximo de espera.
    """
    checar_erros_entre_esperas(driver, ec.presence_of_element_located(locator), timeout)


def pegar_text(driver: Chrome, locator: SeletorHTML) -> str:
    """ Espera um elemento estar presente na página e retorna o texto dentro dele.

    :param driver: Webdriver ativo no momento do clique.
    :param locator: Seletor que representa o elemento HTML que deve ser clicado.
    :return: Texto que estava dentro do elemento HTML.
    """
    esperar_estar_presente(driver, locator)
    return driver.find_element(*locator).text


def apertar_teclas(driver: Chrome, *teclas: str) -> None:
    """ Tecla uma série de teclas.

    :param driver: Webdriver ativo no momento do clique.
    :param teclas: Lista de teclas a serem tecladas.
    """
    for tecla in teclas:
        time.sleep(0.3)
        ActionChains(driver).send_keys(tecla).perform()
