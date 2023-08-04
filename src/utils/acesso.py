import datetime
import time
from sys import maxsize as MAX_INT
from typing import cast

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome

import src.windows as windows
from src.caminhos import Caminhos
from src.erros import ESocialDeslogadoError
from src.utils.python import DEBUG
from src.utils.selenium import esperar_estar_presente

__all__ = ["deslogado", "inicializar_driver", "ocorreu_erro_funcionario", "segundos_restantes_de_sessao", "teste_deslogado"]

def deslogado(driver: Chrome, timeout: int) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located(Caminhos.ESocial.LOGOUT)
        )
    except TimeoutException:
        return False
    else:
        return True


def segundos_restantes_de_sessao(driver: Chrome) -> int:
    esperar_estar_presente(driver, Caminhos.ESocial.TEMPO_SESSAO)
    tempo: str = driver.find_element(*Caminhos.ESocial.TEMPO_SESSAO).text
    try:
        t: time.struct_time = time.strptime(tempo, "%M:%S")
        return int(datetime.timedelta(minutes=t.tm_min, seconds=t.tm_sec).total_seconds())
    except ValueError:
        return MAX_INT


def inicializar_driver() -> Chrome:
    driver = Chrome()
    driver.set_window_rect(x=0, y=0, width=1280, height=720)
    if not DEBUG:
        windows.bloquear_janela(driver)
    return driver


def teste_deslogado(driver: Chrome, timeout: int) -> None:
    if segundos_restantes_de_sessao(driver) <= (10 * 60) or deslogado(driver, timeout):
        raise ESocialDeslogadoError()


def ocorreu_erro_funcionario(driver: Chrome) -> bool:
    # Guardando por precau
    # def mensagem_de_erro_existe() -> bool:
    #     mensagem_de_erro = "Não foi encontrado empregado com o CPF informado."
    #     try:
    #         WebDriverWait(driver, 3).until(
    #             ec.all_of(
    #                 ec.presence_of_element_located(Caminhos.ESocial.Formulario.ERRO_FUNCIONARIO),
    #                 ec.text_to_be_present_in_element(Caminhos.ESocial.Formulario.ERRO_FUNCIONARIO, mensagem_de_erro),
    #             )
    #         )
    #     except TimeoutException:
    #         return False
    #     else:
    #         return True

    def resultado_cpf_encontrado() -> bool:
        esperar_estar_presente(driver, Caminhos.ESocial.CPF_EMPREGADO_INPUT)
        element: WebElement = driver.find_element(*Caminhos.ESocial.CPF_EMPREGADO_INPUT)
        ID = cast(str, element.get_attribute("aria-controls"))
        cpf = cast(str, element.get_attribute("value"))
        css_selector: str = f"#{ID} > li:nth-child(1)".encode().decode()
        try:
            WebDriverWait(driver, 5).until(
                ec.all_of(
                    ec.presence_of_element_located((By.CSS_SELECTOR, css_selector)),
                    ec.text_to_be_present_in_element((By.CSS_SELECTOR, css_selector), cpf),
                )
            )
        except TimeoutException:
            return False
        else:
            return True

    if resultado_cpf_encontrado():
        return False
    return True
