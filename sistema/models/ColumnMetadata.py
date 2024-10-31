from __future__ import annotations

from .Column import Column

import sistema.spreadsheet as sheet

from sistema.spreadsheet import Fill

import re
import math

from collections.abc import Iterable
from typing import Never, get_type_hints

from openpyxl.cell import Cell
from pydantic import BaseModel, model_validator
from unidecode import unidecode_expect_nonascii


class ColumnMetadata(BaseModel):
    """Nomes das propriedades são essenciais para a validação.

    Por uma questão de consistência com o sistema, propriedades serem o mesmo
    texto que as colunas da planilha é algo bom.

    Exemplo de validação (pseudo-código):
    Propriedade: nome_da_mae_do_funcionario
    Passos:
        - coluna.strip()
        - assert coluna.not_empty()
        - coluna.unicode_to_ascii()
        - assert coluna.contains(letters)
        - coluna.lower()
        - coluna.split(nao_alfanumerico)
        - coluna.join('_')
        - assert coluna == propriedade
    """

    @model_validator(mode='before')
    @classmethod
    def _input(cls, data: Iterable[Cell]) -> dict[str, Column] | Never:
        """Validar input e converter valor para string para o formato das keys."""

        assert isinstance(data, Iterable)
        fields = get_type_hints(cls)
        column_count = sum(1 for T in fields.values() if T is Column)
        if column_count == 0:
            raise ValueError('nenhuma coluna foi definida nesse modelo')

        metadata = {}
        for i, cell in enumerate(data):
            assert cell.value != math.nan, 'valor representa célula vazia'
            assert isinstance(cell.value, str), 'valor da célula não é uma string'
            prop = cell.value.strip()
            assert prop != '', 'texto da célula está vazio'
            prop = unidecode_expect_nonascii(prop).lower()
            assert re.search(r'[a-z]', prop), 'texto da célula não contém letras'
            prop = re.sub(r'[^a-z0-9]+', '_', prop).strip('_')
            assert (
                prop in fields
            ), f"modelo {cls.__name__} não contém propriedade '{prop}' referente à coluna '{cell.value}'"
            assert (
                fields[prop] is Column
            ), f"propriedade '{prop}' referente à coluna '{cell.value}' existe, mas não foi definida com o tipo de coluna"

            req_state: sheet.Requirement
            match cell.fill:
                case Fill.RED:
                    req_state = sheet.REQUIRED
                case Fill.TURQUOISE:
                    req_state = sheet.MAYBE
                case Fill.WHITE:
                    req_state = sheet.OPCIONAL
                case _:
                    req_state = sheet.OPCIONAL

            metadata[prop] = {'index': i, 'original_text': cell, 'required': req_state}

        return metadata
