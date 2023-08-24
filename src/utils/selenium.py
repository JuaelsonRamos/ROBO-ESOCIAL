""" Operações úteis e genérias relacionadas ao Selenium."""

import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome

from src.webdriver.tipos import SeletorHTML, Float

__all__ = [
    "TIMEOUT_SECS",
    "apertar_teclas",
    "clicar",
    "escrever",
    "esperar_estar_presente",
    "pegar_text",
]

TIMEOUT_SECS = Float(120.0)
""" Segundos para esperar antes de assumir que a página demorou demais para carregar."""


def clicar(driver: Chrome, locator: SeletorHTML) -> None:
    """Espera o elemento estar disponível e clica nele.

    :param driver: Webdriver ativo no momento do clique.
    :param locator: Seletor que representa o elemento HTML que deve ser clicado.
    """
    WebDriverWait(driver, TIMEOUT_SECS).until(ec.element_to_be_clickable(locator))
    driver.find_element(*locator).click()


def escrever(driver: Chrome, locator: SeletorHTML, *teclas: str) -> None:
    """Espera o elemento estar disponível e escreve nele.

    :param driver: Webdriver ativo no momento do clique.
    :param locator: Seletor que representa o elemento HTML que deve ser clicado.
    :param teclas: Lista de teclas a serem tecladas.
    """
    WebDriverWait(driver, TIMEOUT_SECS).until(ec.element_to_be_clickable(locator))
    driver.find_element(*locator).send_keys(*teclas)


def esperar_estar_presente(driver: Chrome, locator: SeletorHTML) -> None:
    """Espera um elemento HTML estar presente na página.

    :param driver: Webdriver ativo no momento do clique.
    :param locator: Seletor que representa o elemento HTML que deve ser clicado.
    """
    WebDriverWait(driver, TIMEOUT_SECS).until(ec.presence_of_element_located(locator))


def pegar_text(driver: Chrome, locator: SeletorHTML) -> str:
    """Espera um elemento estar presente na página e retorna o texto dentro dele.

    :param driver: Webdriver ativo no momento do clique.
    :param locator: Seletor que representa o elemento HTML que deve ser clicado.
    :return: Texto que estava dentro do elemento HTML.
    """
    esperar_estar_presente(driver, locator)
    return driver.find_element(*locator).text


def apertar_teclas(driver: Chrome, *teclas: str) -> None:
    """Tecla uma série de teclas.

    :param driver: Webdriver ativo no momento do clique.
    :param teclas: Lista de teclas a serem tecladas.
    """
    for tecla in teclas:
        time.sleep(0.3)
        ActionChains(driver).send_keys(tecla).perform()
