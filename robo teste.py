from h11 import InformationalResponse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

# Instala e configura o driver do Chrome automaticamente
driver = webdriver.Chrome(ChromeDriverManager().install())
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pyautogui
import time
import pandas as pd
from openpyxl import Workbook

chrome_driver_path = 'search-ms:displayname=Resultados%20da%20Pesquisa%20em%20Usuários&crumb=location:C%3A%5CUsers\webdriver'
driver = webdriver.Chrome

# Configurar ChromeOptions para usar o certificado digital


chrome_options = Options()
chrome_options.set_capability("acceptInsecureCerts", True)

# Inicializar o ChromeDriver com as opções configuradas
driver = Chrome(options=chrome_options)

driver.get('https://sso.acesso.gov.br/login?client_id=login.esocial.gov.br&authorization_id=188b4b3efd4')

ativar_button = driver.find_element(By.XPATH, '//*[@id="login-acoes"]/div[2]/p/button')
ativar_button.click()


ativar_button = driver.find_element(By.XPATH, '/html/body/div[1]/main/form/div/div[5]/button')
ativar_button.click()

time.sleep(2)
pyautogui.press('enter')
pyautogui.press('down')




ativar_button = driver.find_element(By.XPATH, '//*[@id="header"]/div[2]/a')
ativar_button.click()

# ESCOLHA DE CNPJ, LER PLANILHA PRIMEIRO
  
ativar_button = driver.find_element(By.XPATH, '//*[@id="perfilAcesso"]')
ativar_button.click()

pyautogui.press('down', presses=2)
pyautogui.press('enter')

#  retirar cnpj de teste 

ativar_button = driver.find_element(By.XPATH, '//*[@id="procuradorCnpj"]').send_keys("32.721.153/0001-14")
ativar_button = driver.find_element(By.XPATH, '//*[@id="btn-verificar-procuracao-cnpj"]')
ativar_button.click()
time.sleep(2)
ativar_button = driver.find_element(By.XPATH, '/html/body/div[3]/div[4]/div/form/div/section/div[7]/div[2]/div[6]')
ativar_button.click()

time.sleep(5)

ativar_button = driver.find_element(By.XPATH, '//html/body/div[1]/div[2]/div[1]/nav/button')
ativar_button.click()
ativar_button = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/nav/div/ul/li[1]/a')
ativar_button.click()
ativar_button = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div/div/div/div/div/div/div/input').send_keys('120.438.827-08')
time.sleep(2)
pyautogui.press('enter')
# Ler a planilha existente
tabela_atualizada = pd.read_excel('alfa.xlsx')

# Encontrar o elemento desejado
elemento = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div/fieldset/div/div[3]/div/div[2]/ul')

# Obter o texto do elemento
informacao = elemento.text

# Dividir as informações por quebra de linha
linhas = informacao.split('\n')

# Extrair as informações relevantes
situacao = linhas[2]
data_admissao = linhas[2]
data_nascimento = linhas[2]
matricula = linhas[2]
data_desligamento = linhas[2]

# Preencher as informações nas colunas correspondentes
tabela_atualizada['Situação'] = situacao
tabela_atualizada['Dt.Admissão'] = data_admissao
tabela_atualizada['Dt.Nascimento'] = data_nascimento
tabela_atualizada['Matrícula'] = matricula
tabela_atualizada['Dt.Demissão'] = data_desligamento

# Salvar o DataFrame atualizado na planilha Excel
tabela_atualizada.to_excel('informacoes.xlsx', index=False)



