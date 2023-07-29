from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
import time

from tipos import SeletorHTML

TIMEOUT_SECS: float = 120.0

def clicar(driver: Chrome, locator: SeletorHTML) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(
        ec.element_to_be_clickable(locator))
    driver.find_element(*locator).click()

def escrever(driver: Chrome, locator: SeletorHTML, *teclas) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(
        ec.element_to_be_clickable(locator))
    driver.find_element(*locator).send_keys(*teclas)

def esperar_estar_presente(driver: Chrome, locator: SeletorHTML) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(
        ec.presence_of_element_located(locator))

def pegar_text(driver: Chrome, locator: SeletorHTML) -> str:
    esperar_estar_presente(driver, locator)
    return driver.find_element(*locator).text

def apertar_teclas(driver: Chrome, *teclas) -> None:
    for tecla in teclas:
        time.sleep(.3)
        ActionChains(driver).send_keys(tecla).perform()