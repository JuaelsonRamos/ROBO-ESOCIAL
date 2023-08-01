from dataclasses import dataclass
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from undetected_chromedriver import Chrome
from unidecode import unidecode
from contextlib import suppress

from src.tipos import SeletorHTML as sh
from src.utils.selenium import esperar_estar_presente

class DadoNaoEncontrado(Exception): pass

class FuncionarioCrawlerBase:
    _rotulos_seletor: sh
    _valores_seletor: sh

    def __init__(self, driver: Chrome) -> None:
        esperar_estar_presente(driver, self._rotulos_seletor)
        esperar_estar_presente(driver, self._valores_seletor)
        self.rotulos = [elem.text for elem in driver.find_elements(*self._rotulos_seletor)]
        self.rotulos_normalizado = [unidecode(rotulo).lower() for rotulo in self.rotulos]
        self.valores = [elem.text for elem in driver.find_elements(*self._valores_seletor)]

    def _get_dado(self, padrao: str) -> str:
        """Se o rotulo contém o padrão especificado, retorne seu valor. padrao pode ser
        uma versão em minusculo e sem acento do texto ou o texto exato.
        
            raises DadoNaoEncontrado
                Caso o padrão não tenha sido encontrado em nenhum rótulo."""
        for i in range(len(self.rotulos)):
            # for loop é aceitável pq a quantidade de itens é bem pequena
            if padrao in self.rotulos_normalizado[i] or padrao in self.rotulos[i]:
                return self.valores[i]
        raise DadoNaoEncontrado(padrao)

    @property
    def SITUACAO(self) -> str:
        return self._get_dado("situacao")
    
    @property
    def NASCIMENTO(self) -> str:
        return self._get_dado("nascimento")
    
    @property
    def DEMISSAO(self) -> str:
        return self._get_dado("desligamento")
    
    @property
    def ADMISSAO(self) -> str:
        return self._get_dado("admissao")
    
    @property
    def MATRICULA(self) -> str:
        return self._get_dado("matricula")

@dataclass(init=False, frozen=True)
class Caminhos:
    class Govbr:
        SELECIONAR_CERTIFICADO: sh = (By.CSS_SELECTOR, '#cert-digital button[type=submit]')

    class ESocial:
        BOTAO_LOGIN: sh = (By.CSS_SELECTOR, '#login-acoes button.sign-in')
        TROCAR_PERFIL: sh = (By.CLASS_NAME, 'alterar-perfil')
        ACESSAR_PERFIL: sh = (By.ID, 'perfilAcesso')
        CNPJ_INPUT: sh = (By.ID, 'procuradorCnpj')
        CNPJ_INPUT_CONFIRMAR: sh = (By.ID, 'btn-verificar-procuracao-cnpj')
        CNPJ_SELECIONAR_MODULO: sh = (By.CSS_SELECTOR, '#comSelecaoModulo .modulos #sst')
        MENU_TRABALHADOR: sh = (By.CSS_SELECTOR, 'nav:first-child button[aria-haspopup=true]')
        MENU_OPCAO_EMPREGADOS: sh = (By.CSS_SELECTOR, 'nav:first-child [role=menu] [role=menuitem] a[href$=gestaoTrabalhadores]')
        CPF_EMPREGADO_INPUT: sh = (By.CSS_SELECTOR, 'div[label*=CPF] input[type=text]')
        DESLOGAR: sh = (By.CSS_SELECTOR, 'div.logout a')
        # botão de deslogar está localizado em um lugar diferente se vc partir da tela de login com cnpj
        DESLOGAR_CNPJ_INPUT: sh = (By.ID, 'sairAplicacao')
        LOGOUT: sh = (By.CLASS_NAME, 'logout-sucesso')
        TEMPO_SESSAO: sh = (By.CLASS_NAME, 'tempo-sessao')

        class Formulario(FuncionarioCrawlerBase):
            _rotulos_seletor: sh = (By.CSS_SELECTOR, "div[role=tabpanel] ul li .MuiListItemText-primary")
            _valores_seletor: sh = (By.CSS_SELECTOR, "div[role=tabpanel] ul li .MuiListItemText-secondary")
            
            ERRO_FUNCIONARIO: sh = (By.CSS_SELECTOR, '#mensagens-gerais div[role=alert] .MuiAlert-message')

        class Lista(FuncionarioCrawlerBase):
            _clicaveis_seletor: sh = (By.CSS_SELECTOR, "#div-gestao-trabalhadores fieldset:first-child .MuiGrid-item")
            _cpfs_seletor: sh = (By.CSS_SELECTOR, "#div-gestao-trabalhadores fieldset:first-child .MuiGrid-item .MuiCardContent-root p:last-child")
            _rotulos_seletor: sh = (By.CSS_SELECTOR, "div[role=tabpanel] ul li .MuiListItemText-primary")
            _valores_seletor: sh = (By.CSS_SELECTOR, "div[role=tabpanel] ul li .MuiListItemText-secondary")

            def __init__(self, driver: Chrome) -> None:
                esperar_estar_presente(driver, self._clicaveis_seletor)
                esperar_estar_presente(driver, self._cpfs_seletor)
                self.driver = driver
                self.clicaveis = driver.find_elements(*self._clicaveis_seletor)
                self.quantos = len(self.clicaveis)
                self.cpfs = [elem.text for elem in driver.find_elements(*self._cpfs_seletor)]

            def proximo_funcionario(self) -> str:
                """Toda vez que é executado prepara o objeto com os dados do próximo funcionário."""
                for i in range(self.quantos):
                    self.clicaveis[i].click()
                    super().__init__(self.driver)
                    yield self.cpfs[i]

            @classmethod
            def testar(self, driver: Chrome) -> bool:
                """Checa se a seleção de funcionários se apresenta em formato de lista."""
                try:
                    driver.find_element(By.ID, "div-pesquisa")
                except NoSuchElementException:
                    return True
                else:
                    return False