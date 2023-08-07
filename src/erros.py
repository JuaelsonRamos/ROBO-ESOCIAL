""" Erros genéricos ou que devem ser acessíveis de todos os módulos, evitando erros de dependências
circulares."""

__all__ = ["ESocialDeslogadoError", "FuncionarioNaoEncontradoError"]

class FuncionarioNaoEncontradoError(Exception):
    """ Erro para quando os dados do funcionário não são encontrados ou não carregam a tempo."""


class ESocialDeslogadoError(Exception):
    """ Erro para quando o site do ESocial é deslogado por quaisquer motivos."""
