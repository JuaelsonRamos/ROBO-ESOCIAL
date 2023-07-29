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
import windows

@dataclass(init=False, frozen=True)
class Caminhos:
    ESOCIAL_BOTAO_LOGIN: Localizador = (By.CSS_SELECTOR, '#login-acoes button.sign-in')
    SELECIONAR_CERTIFICADO: Localizador = (By.CSS_SELECTOR, '#cert-digital button[type=submit]')
    ESOCIAL_TROCAR_PERFIL: Localizador = (By.CLASS_NAME, 'alterar-perfil')
    ESOCIAL_ACESSAR_PERFIL: Localizador = (By.ID, 'perfilAcesso')
    ESOCIAL_CNPJ_INPUT: Localizador = (By.ID, 'procuradorCnpj')
    ESOCIAL_CNPJ_INPUT_CONFIRMAR: Localizador = (By.ID, 'btn-verificar-procuracao-cnpj')
    ESOCIAL_CNPJ_SELECIONAR_MODULO: Localizador = (By.CSS_SELECTOR, '#comSelecaoModulo .modulos #sst')
    ESOCIAL_MENU_TRABALHADOR: Localizador = (By.CSS_SELECTOR, 'nav:first-child button[aria-haspopup=true]')
    ESOCIAL_MENU_OPCAO_EMPREGADOS: Localizador = (By.CSS_SELECTOR, 'nav:first-child [role=menu] [role=menuitem] a[href$=gestaoTrabalhadores]')
    ESOCIAL_CPF_EMPREGADO_INPUT: Localizador = (By.CSS_SELECTOR, 'div[label*=CPF] input[type=text]')
    ESOCIAL_DESLOGAR: Localizador = (By.CSS_SELECTOR, 'div.logout a')
    # botão de deslogar está localizado em um lugar diferente se vc partir da tela de login com cnpj
    ESOCIAL_DESLOGAR_CNPJ_INPUT: Localizador = (By.ID, 'sairAplicacao')
    ESOCIAL_LOGOUT: Localizador = (By.CLASS_NAME, 'logout-sucesso')
    ESOCIAL_TEMPO_SESSAO: Localizador = (By.CLASS_NAME, 'tempo-sessao')

    # Raspagem de dados
    DADOS_SITUACAO: Localizador = (By.CSS_SELECTOR, 'div[role=tabpanel] ul li:first-child p')
    DADOS_NASCIMENTO: Localizador = (By.CSS_SELECTOR, 'div[role=tabpanel] ul li:nth-child(11) p')
    DADOS_DESLIGAMENTO: Localizador = (By.CSS_SELECTOR, 'div[role=tabpanel] ul li:nth-child(10) p')
    DADOS_ADMISSAO: Localizador = (By.CSS_SELECTOR, 'div[role=tabpanel] ul li:nth-child(9) p')
    DADOS_MATRICULA: Localizador = (By.CSS_SELECTOR, 'div[role=tabpanel] ul li:nth-child(2) p')

    ERRO_FUNCIONARIO: Localizador = (By.CSS_SELECTOR, '#mensagens-gerais div[role=alert] .MuiAlert-message')


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
        
def inicializar_driver() -> Chrome:
    driver = Chrome()
    driver.set_window_rect(x=0, y=0, width=1280, height=720)
    windows.bloquear_janela(driver)
    return driver