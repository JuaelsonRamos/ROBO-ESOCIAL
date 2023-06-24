from selenium import webdriver
from selenium.webdriver.support import wait, expected_conditions
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from dataclasses import dataclass
# from selenium.webdriver.support import expected_conditions as EC
import pyautogui
import time
import pandas as pd

LINK_PRINCIPAL = 'https://sso.acesso.gov.br/login?client_id=login.esocial.gov.br&authorization_id=188b4b3efd4'

@dataclass(init=False, frozen=True)
class Caminhos:
    ESOCIAL_BOTAO_LOGIN: str = '//*[@id="login-acoes"]/div[2]/p/button'
    SELECIONAR_CERTIFICADO: str = '//*[@id="cert-digital"]/button'
    ESOCIAL_TROCAR_PERFIL: str = '//*[@id="header"]/div[2]/a'
    ESOCIAL_ACESSAR_PERFIL: str = '//*[@id="perfilAcesso"]'
    ESOCIAL_CNPJ_INPUT: str = '//*[@id="procuradorCnpj"]'
    ESOCIAL_CNPJ_INPUT_CONFIRMAR: str = '//*[@id="btn-verificar-procuracao-cnpj"]'
    ESOCIAL_CNPJ_SELECIONAR_MODULO: str = '/html/body/div[3]/div[4]/div/form/div/section/div[7]/div[2]/div[6]'
    ESOCIAL_MENU_TRABALHADOR: str = '//html/body/div[1]/div[2]/div[1]/nav/button'
    ESOCIAL_MENU_OPCAO_EMPREGADOS: str = '/html/body/div[1]/div[2]/div[1]/nav/div/ul/li[1]/a'
    ESOCIAL_CPF_EMPREGADO_INPUT: str = '/html/body/div[1]/div[2]/div[1]/div/div/div/div/div/div/div/div/input'

driver = webdriver.Chrome('C:\chromedriver_win32 (2)')
wait = WebDriverWait(driver, 20)
#  retirar cnpj de teste 
# Ler o arquivo Excel e armazenar em um DataFrame
tabela = pd.read_excel("alfa.xlsx", header=None)
#display(tabela)

# Acessar o nome da coluna na segunda linha


# Acessar os valores da coluna específica pelo índice numérico
coluna1 = tabela.iloc[2:, 54].values
coluna2 = tabela.iloc[2:, 19].values
# Exibir os valores da coluna
# print(coluna1)
# print(coluna2)

# Iterar sobre os valores da coluna
# for CNPJ in coluna1:
    # Faça algo com cada valor de CNPJ
    # print(CNPJ)

if len(coluna1) != len(coluna2):
    raise ValueError(f"Não há a 1 cnpj para cada cpf, {len(coluna1)} cnpjs para {len(coluna2)} cpfs.")

    # Montando toda a estrutura do código
for CNPJ, CPF in zip(coluna1, coluna2):
    # valor_coluna1 = CNPJ
    # Faça algo com cada valor de CNPJ da coluna específica

    driver.get(LINK_PRINCIPAL)

    ativar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_BOTAO_LOGIN)
    ativar_button.click()
    time.sleep(2)
    ativar_button = driver.find_element(By.XPATH, Caminhos.SELECIONAR_CERTIFICADO)
    ativar_button.click()

    # Aguarde algum tempo após o clique (opcional)
    time.sleep(3)

    ativar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_TROCAR_PERFIL)
    ativar_button.click()
    time.sleep(2)

    # ESCOLHA DE CNPJ, LER PLANILHA PRIMEIRO
    ativar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_ACESSAR_PERFIL)
    ativar_button.click()
    time.sleep(2)

    pyautogui.press('down', presses=2)
    pyautogui.press('enter')

    ativar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_CNPJ_INPUT).send_keys(CNPJ)
    ativar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_CNPJ_INPUT_CONFIRMAR)
    ativar_button.click()
    time.sleep(2)
    ativar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_CNPJ_SELECIONAR_MODULO)
    ativar_button.click()

    time.sleep(5)

    ativar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_MENU_TRABALHADOR)
    ativar_button.click()
    ativar_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_MENU_OPCAO_EMPREGADOS)
    ativar_button.click()
    time.sleep(5)

    input_button = driver.find_element(By.XPATH, Caminhos.ESOCIAL_CPF_EMPREGADO_INPUT)
    input_button.send_keys(CPF)
    time.sleep(2)
    pyautogui.press('enter')

    pass # debug
# Ler a planilha novamente

tabela_atualizada = pd.read_excel('informacoes.xlsx')

# Acessar os valores da coluna específica pelo índice numérico
coluna2 = tabela_atualizada.iloc[2:, 19].values

# Iterar sobre os valores da coluna

    # Montando toda a estrutura do código
tabela_atualizada = tabela.copy()
for linha, CPF in enumerate(tabela_atualizada.iloc[2:, 19].values):
    valor_coluna2 = CPF
    time.sleep(2)
    # Preencher o campo de CPF
    campo_cpf = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div/div/div/div/div/div/div/input').send_keys(CPF)
   
    elemento = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul')  # Substitua pelo seletor do elemento desejado
informacao = elemento.text  # Obtém o texto do elemento

dados = pd.DataFrame({'Informacao': [informacao]})
dados.to_excel('informacoes.xlsx', index=False)  # Grava as informações em um arquivo Excel