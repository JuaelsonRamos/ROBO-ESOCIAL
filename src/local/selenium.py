from dataclasses import dataclass
import datetime
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from undetected_chromedriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
import time
from sys import maxsize as MAX_INT
from tipos import Localizador

@dataclass(init=False, frozen=True)
class Caminhos:
    ESOCIAL_BOTAO_LOGIN: Localizador = (By.XPATH, '//*[@id="login-acoes"]/div[2]/p/button')
    SELECIONAR_CERTIFICADO: Localizador = (By.XPATH, '//*[@id="cert-digital"]/button')
    ESOCIAL_TROCAR_PERFIL: Localizador = (By.XPATH, '//*[@id="header"]/div[2]/a')
    ESOCIAL_ACESSAR_PERFIL: Localizador = (By.XPATH, '//*[@id="perfilAcesso"]')
    ESOCIAL_CNPJ_INPUT: Localizador = (By.XPATH, '//*[@id="procuradorCnpj"]')
    ESOCIAL_CNPJ_INPUT_CONFIRMAR: Localizador = (By.XPATH, '//*[@id="btn-verificar-procuracao-cnpj"]')
    ESOCIAL_CNPJ_SELECIONAR_MODULO: Localizador = (By.XPATH, '/html/body/div[3]/div[4]/div/form/div/section/div[7]/div[2]/div[6]')
    ESOCIAL_MENU_TRABALHADOR: Localizador = (By.XPATH, '//html/body/div[1]/div[2]/div[1]/nav/button')
    ESOCIAL_MENU_OPCAO_EMPREGADOS: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/nav/div/ul/li[1]/a')
    ESOCIAL_CPF_EMPREGADO_INPUT: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div/div/div/div/div/div/div/input')
    ESOCIAL_DESLOGAR: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/header/div[2]/div[2]/span/a')
    # botão de deslogar está localizado em um lugar diferente se vc partir da tela de login com cnpj
    ESOCIAL_DESLOGAR_CNPJ_INPUT: Localizador = (By.XPATH, '/html/body/div[3]/div[1]/div[3]')
    ESOCIAL_LOGOUT: Localizador = (By.CLASS_NAME, 'logout-sucesso')
    ESOCIAL_TEMPO_SESSAO: Localizador = (By.CLASS_NAME, 'tempo-sessao')

    # Raspagem de dados
    DADOS_SITUACAO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[1]/div/p')
    DADOS_NASCIMENTO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[8]/div/p')
    DADOS_DESLIGAMENTO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[8]/div/p')
    DADOS_ADMISSAO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[7]/div/p')
    DADOS_MATRICULA: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[2]/div/p')

    ERRO_FUNCIONARIO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[1]/div/div[2]')


TIMEOUT_SECS: float = 120.0

def clicar(driver: Chrome, locator: Localizador) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(
        ec.element_to_be_clickable(locator))
    driver.find_element(*locator).click()

def escrever(driver: Chrome, locator: Localizador, *teclas) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(
        ec.element_to_be_clickable(locator))
    driver.find_element(*locator).send_keys(*teclas)

def esperar_estar_presente(driver: Chrome, locator: Localizador) -> None:
    WebDriverWait(driver, TIMEOUT_SECS).until(
        ec.presence_of_element_located(locator))

def pegar_text(driver: Chrome, locator: Localizador) -> str:
    esperar_estar_presente(driver, locator)
    return driver.find_element(*locator).text

def apertar_teclas(driver: Chrome, *teclas) -> None:
    for tecla in teclas:
        time.sleep(.3)
        ActionChains(driver).send_keys(tecla).perform()


def deslogado(driver: Chrome, timeout: int) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located(Caminhos.ESOCIAL_LOGOUT))
    except TimeoutException: return False
    else: return True

def segundos_restantes_de_sessao(driver: Chrome) -> int:
    esperar_estar_presente(driver, Caminhos.ESOCIAL_TEMPO_SESSAO)
    tempo: str = driver.find_element(*Caminhos.ESOCIAL_TEMPO_SESSAO).text
    try:
        t: time.struct_time = time.strptime(tempo, "%M:%S")
        return int(datetime
                   .timedelta(minutes=t.tm_min, seconds=t.tm_sec)
                   .total_seconds())
    except:
        # principalmente caso o contador ainda não estiver na tela
        return MAX_INT
        