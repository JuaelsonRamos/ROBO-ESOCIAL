from __future__ import annotations

from sistema.models.Coluna import Coluna, Required

import re
import math

from typing import Any, Never, cast, get_type_hints

from pydantic import BaseModel, model_validator
from unidecode import unidecode_expect_nonascii


class ColunaModel(BaseModel):
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
    def _input(cls, data: Any) -> list[str] | Never:
        """Validar input e converter valor para string para o formato das keys."""
        assert isinstance(
            data, list
        ), 'dados providos não representam uma linha da planilha (lista de células)'
        data = cast(list, data)
        fields = get_type_hints(cls)
        metadata = {}
        for i, text in enumerate(data):
            assert text != math.nan, 'valor representa célula vazia'
            assert isinstance(text, str), 'valor da célula não é uma string'
            prop = text.strip()
            assert prop != '', 'texto da célula está vazio'
            prop = unidecode_expect_nonascii(prop).lower()
            assert re.search(r'[a-zA-Z]', prop), 'texto da célula não contém letras'
            prop = re.sub(r'[^a-zA-Z0-9]+', '_', prop).strip('_')
            assert (
                prop in fields
            ), f"modelo {cls.__name__} não contém propriedade '{prop}' referente à coluna '{text}'"
            assert (
                fields[prop] is Coluna
            ), f"propriedade '{prop}' referente à coluna '{text}' existe, mas não foi definida com o tipo de coluna"
            metadata[prop] = {
                'index': i,
                'original_text': text,
                'required': Required.OPCIONAL,  # TODO Identificar se a coluna é necessária
            }
        return metadata
