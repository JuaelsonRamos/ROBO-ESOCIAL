from dataclasses import dataclass

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from undetected_chromedriver import Chrome
from unidecode import unidecode
from typing import List, Generator

from src.tipos import SeletorHTML, Int
from src.utils.selenium import esperar_estar_presente

__all__ = ["Caminhos", "DadoNaoEncontrado", "FuncionarioCrawlerBase"]


class DadoNaoEncontrado(Exception):
    pass


class FuncionarioCrawlerBase:
    _rotulos_seletor: SeletorHTML
    _valores_seletor: SeletorHTML

    def __init__(self, driver: Chrome) -> None:
        esperar_estar_presente(driver, self._rotulos_seletor)
        esperar_estar_presente(driver, self._valores_seletor)
        self.rotulos: List[str] = [elem.text for elem in driver.find_elements(*self._rotulos_seletor)]
        self.rotulos_normalizado: List[str] = [unidecode(rotulo).lower() for rotulo in self.rotulos]
        self.valores: List[str] = [elem.text for elem in driver.find_elements(*self._valores_seletor)]

    def _get_dado(self, padrao: str) -> str:
        """ Se o rotulo contém o padrão especificado, retorne seu valor.

        :param padrao: Versão em minusculo e sem acento do texto ou o texto exato.
        :raises DadoNaoEncontrado: Caso o padrão não tenha sido encontrado em nenhum rótulo.
        """
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
        SELECIONAR_CERTIFICADO: SeletorHTML = (By.CSS_SELECTOR, "#cert-digital button[type=submit]")

    class ESocial:
        BOTAO_LOGIN: SeletorHTML = (By.CSS_SELECTOR, "#login-acoes button.sign-in")
        TROCAR_PERFIL: SeletorHTML = (By.CLASS_NAME, "alterar-perfil")
        ACESSAR_PERFIL: SeletorHTML = (By.ID, "perfilAcesso")
        CNPJ_INPUT: SeletorHTML = (By.ID, "procuradorCnpj")
        CNPJ_INPUT_CONFIRMAR: SeletorHTML = (By.ID, "btn-verificar-procuracao-cnpj")
        CNPJ_SELECIONAR_MODULO: SeletorHTML = (By.CSS_SELECTOR, "#comSelecaoModulo .modulos #sst")
        MENU_TRABALHADOR: SeletorHTML = (By.CSS_SELECTOR, "nav:first-child button[aria-haspopup=true]")
        MENU_OPCAO_EMPREGADOS: SeletorHTML = (
            By.CSS_SELECTOR,
            "nav:first-child [role=menu] [role=menuitem] a[href$=gestaoTrabalhadores]",
        )
        CPF_EMPREGADO_INPUT: SeletorHTML = (By.CSS_SELECTOR, "div[label*=CPF] input[type=text]")
        DESLOGAR: SeletorHTML = (By.CSS_SELECTOR, "div.logout a")
        # botão de deslogar está localizado em um lugar diferente se vc partir da tela de login com cnpj
        DESLOGAR_CNPJ_INPUT: SeletorHTML = (By.ID, "sairAplicacao")
        LOGOUT: SeletorHTML = (By.CLASS_NAME, "logout-sucesso")
        TEMPO_SESSAO: SeletorHTML = (By.CLASS_NAME, "tempo-sessao")

        class Formulario(FuncionarioCrawlerBase):
            _rotulos_seletor: SeletorHTML = (
                By.CSS_SELECTOR,
                "div[role=tabpanel] ul li .MuiListItemText-primary",
            )
            _valores_seletor: SeletorHTML = (
                By.CSS_SELECTOR,
                "div[role=tabpanel] ul li .MuiListItemText-secondary",
            )

            ERRO_FUNCIONARIO: SeletorHTML = (
                By.CSS_SELECTOR,
                "#mensagens-gerais div[role=alert] .MuiAlert-message",
            )

        class Lista(FuncionarioCrawlerBase):
            _clicaveis_seletor: SeletorHTML = (
                By.CSS_SELECTOR,
                "#div-gestao-trabalhadores fieldset:first-child .MuiGrid-item",
            )
            _cpfs_seletor: SeletorHTML = (
                By.CSS_SELECTOR,
                "#div-gestao-trabalhadores fieldset:first-child .MuiGrid-item .MuiCardContent-root p:last-child",
            )
            _rotulos_seletor: SeletorHTML = (
                By.CSS_SELECTOR,
                "div[role=tabpanel] ul li .MuiListItemText-primary",
            )
            _valores_seletor: SeletorHTML = (
                By.CSS_SELECTOR,
                "div[role=tabpanel] ul li .MuiListItemText-secondary",
            )

            def __init__(self, driver: Chrome) -> None: # pylint: disable=super-init-not-called
                esperar_estar_presente(driver, self._clicaveis_seletor)
                esperar_estar_presente(driver, self._cpfs_seletor)
                self.driver = driver
                self.clicaveis: List[WebElement] = driver.find_elements(*self._clicaveis_seletor)
                self.quantos = Int(len(self.clicaveis))
                self.cpfs: List[str] = [elem.text for elem in driver.find_elements(*self._cpfs_seletor)]

            def proximo_funcionario(self) -> Generator[str, None, None]:
                """ Toda vez que é executado prepara o objeto com os dados do próximo
                funcionário."""
                for i in range(self.quantos):
                    self.clicaveis[i].click()
                    super().__init__(self.driver)
                    yield self.cpfs[i]

            @classmethod
            def testar(cls, driver: Chrome) -> bool:
                """ Checa se a seleção de funcionários se apresenta em formato de lista."""
                try:
                    driver.find_element(By.ID, "div-pesquisa")
                except NoSuchElementException:
                    return True
                else:
                    return False
