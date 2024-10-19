from __future__ import annotations

import pytest

from sistema.models.ColunaModel import Coluna, ColunaModel

import math
import random

from typing import Any

import faker

from pydantic import ValidationError


columns: list[str] = [
    'Etiam consectetur, lacus.',
    'Sed lectus ex.',
    'Vivamus pharetra libero.',
    'Suspendisse semper eros.',
    'Donec bibendum urna.',
    'Pellentesque eu nisl.',
]


class MyModel(ColunaModel):
    etiam_consectetur_lacus: Coluna
    sed_lectus_ex: Coluna
    vivamus_pharetra_libero: Coluna
    suspendisse_semper_eros: Coluna
    donec_bibendum_urna: Coluna
    pellentesque_eu_nisl: Coluna


def test_input_parsing():
    global columns

    with pytest.raises(ValidationError):
        MyModel.model_validate(None)
    with pytest.raises(ValidationError):
        MyModel.model_validate('Lorem ipsum, dolor sit amet')
    with pytest.raises(ValidationError):
        MyModel.model_validate(123)
    with pytest.raises(ValidationError):
        # Relacionado a algumas bibliotecas que lêm excel
        MyModel.model_validate(math.nan)

    assert MyModel.model_validate(columns)

    def change_random(data: list, value: Any):
        other = data.copy()
        rand_index = random.randrange(1, len(other))
        other[rand_index] = value
        return other

    # Valores inválidos
    with pytest.raises(ValidationError):
        MyModel.model_validate(change_random(columns, math.nan))
    with pytest.raises(ValidationError):
        MyModel.model_validate(change_random(columns, None))
    with pytest.raises(ValidationError):
        MyModel.model_validate(change_random(columns, 123))
    with pytest.raises(ValidationError):
        MyModel.model_validate(change_random(columns, ''))

    with pytest.raises(ValidationError):
        # Valores válidos, conteúdo inválido
        MyModel.model_validate(change_random(columns, '., -'))
