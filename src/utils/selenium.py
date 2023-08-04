import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome

from src.tipos import SeletorHTML, Float

__all__ = ["TIMEOUT_SECS", "apertar_teclas", "clicar", "escrever", "esperar_estar_presente", "pegar_text"]

TIMEOUT_SECS = Float(120.0)


def clicar(driver: Chrome, locator: SeletorHTML) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(ec.element_to_be_clickable(locator))
    driver.find_element(*locator).click()


def escrever(driver: Chrome, locator: SeletorHTML, *teclas: str) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(ec.element_to_be_clickable(locator))
    driver.find_element(*locator).send_keys(*teclas)


def esperar_estar_presente(driver: Chrome, locator: SeletorHTML) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(ec.presence_of_element_located(locator))


def pegar_text(driver: Chrome, locator: SeletorHTML) -> str:
    esperar_estar_presente(driver, locator)
    return driver.find_element(*locator).text


def apertar_teclas(driver: Chrome, *teclas: str) -> None:
    for tecla in teclas:
        time.sleep(0.3)
        ActionChains(driver).send_keys(tecla).perform()
