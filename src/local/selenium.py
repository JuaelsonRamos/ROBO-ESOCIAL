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
class _Caminhos_ESOCIAL_Formulario_Dados:
    """Caminhos HTML para a localização dos dados do funcionário
    uma vez que ele tenha sido encontrado através do formulário."""
    SITUACAO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[1]/div/p')
    NASCIMENTO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[8]/div/p')
    DESLIGAMENTO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[8]/div/p')
    ADMISSAO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[7]/div/p')
    MATRICULA: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul/li[2]/div/p')
    ERRO_FUNCIONARIO: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[1]/div/div[2]')

@dataclass(init=False, frozen=True)
class _Caminhos_ESOCIAL_Formulario:
    """Caminhos HTML para a raspagem de Dados caso o método
    de seleção de funcionários seja o formulário."""
    Dados = _Caminhos_ESOCIAL_Formulario_Dados
    CPF_EMPREGADO_INPUT: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div/div/div/div/div/div/div/input')
    DESLOGAR: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/header/div[2]/div[2]/span/a')

@dataclass(init=False, frozen=True)
class _Caminhos_ESOCIAL_Lista_Dados:
    """Caminhos HTML para a localização dos dados do funcionário
    uma vez que ele tenha sido encontrado através da lista."""
    pass

@dataclass(init=False, frozen=True)
class _Caminhos_ESOCIAL_Lista:
    """Caminhos HTML para a raspagem de Dados caso o método
    de seleção de funcionários seja a lista."""
    Dados = _Caminhos_ESOCIAL_Lista_Dados

@dataclass(init=False, frozen=True)
class _Caminhos_GOVBR:
    SELECIONAR_CERTIFICADO: Localizador = (By.XPATH, '//*[@id="cert-digital"]/button')

@dataclass(init=False, frozen=True)
class _Caminhos_ESOCIAL:
    """Caminhos HTML para o site do ESocial."""
    Formulario = _Caminhos_ESOCIAL_Formulario
    Lista = _Caminhos_ESOCIAL_Lista
    BOTAO_LOGIN: Localizador = (By.XPATH, '//*[@id="login-acoes"]/div[2]/p/button')
    TROCAR_PERFIL: Localizador = (By.XPATH, '//*[@id="header"]/div[2]/a')
    ACESSAR_PERFIL: Localizador = (By.XPATH, '//*[@id="perfilAcesso"]')
    CNPJ_INPUT: Localizador = (By.XPATH, '//*[@id="procuradorCnpj"]')
    CNPJ_INPUT_CONFIRMAR: Localizador = (By.XPATH, '//*[@id="btn-verificar-procuracao-cnpj"]')
    CNPJ_SELECIONAR_MODULO: Localizador = (By.XPATH, '/html/body/div[3]/div[4]/div/form/div/section/div[7]/div[2]/div[6]')
    # botão de deslogar está localizado em um lugar diferente se vc partir da tela de login com cnpj
    DESLOGAR_CNPJ_INPUT: Localizador = (By.XPATH, '/html/body/div[3]/div[1]/div[3]')
    MENU_TRABALHADOR: Localizador = (By.XPATH, '//html/body/div[1]/div[2]/div[1]/nav/button')
    MENU_OPCAO_EMPREGADOS: Localizador = (By.XPATH, '/html/body/div[1]/div[2]/div[1]/nav/div/ul/li[1]/a')
    LOGOUT: Localizador = (By.CLASS_NAME, 'logout-sucesso')
    TEMPO_SESSAO: Localizador = (By.CLASS_NAME, 'tempo-sessao')

@dataclass(init=False, frozen=True)
class Caminhos:
    ESOCIAL = _Caminhos_ESOCIAL
    GOVBR = _Caminhos_GOVBR

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
            ec.presence_of_element_located(Caminhos.ESOCIAL.LOGOUT))
    except TimeoutException: return False
    else: return True

def segundos_restantes_de_sessao(driver: Chrome) -> int:
    esperar_estar_presente(driver, Caminhos.ESOCIAL.TEMPO_SESSAO)
    tempo: str = driver.find_element(*Caminhos.ESOCIAL.TEMPO_SESSAO).text
    try:
        t: time.struct_time = time.strptime(tempo, "%M:%S")
        return int(datetime
                   .timedelta(minutes=t.tm_min, seconds=t.tm_sec)
                   .total_seconds())
    except:
        # principalmente caso o contador ainda não estiver na tela
        return MAX_INT
        