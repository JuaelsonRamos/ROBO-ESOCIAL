from __future__ import annotations

from .Column import Column
from .ColumnMetadata import ColumnMetadata

import pytest

from testing import change_random, fake_sheet

import sistema.spreadsheet as sheet

import math

from pydantic import ValidationError


def test_input_parsing():
    columns = [
        {'text': 'Etiam consectetur, lacus.', 'required': sheet.REQUIRED},
        {'text': 'Sed lectus ex.', 'required': sheet.OPCIONAL},
        {'text': 'Vivamus pharetra libero.', 'required': sheet.MAYBE},
        {'text': 'Suspendisse semper eros.', 'required': sheet.MAYBE},
        {'text': 'Donec bibendum urna.', 'required': sheet.OPCIONAL},
        {'text': 'Pellentesque eu nisl.', 'required': sheet.REQUIRED},
    ]

    class MyModel(ColumnMetadata):
        etiam_consectetur_lacus: Column
        sed_lectus_ex: Column
        vivamus_pharetra_libero: Column
        suspendisse_semper_eros: Column
        donec_bibendum_urna: Column
        pellentesque_eu_nisl: Column

    _nonsense = [None, 123, math.nan, 'string', columns]

    for error_value in _nonsense:
        with pytest.raises(ValidationError):
            MyModel.model_validate(error_value)

    with fake_sheet(model=1, headers=columns) as fs:
        cells = next(fs.active.iter_rows(min_row=2, max_row=2))

        for error_value in _nonsense:
            with pytest.raises(ValidationError):
                MyModel.model_validate(change_random(cells, error_value))
        with pytest.raises(ValidationError):
            # Texto não contém letras
            MyModel.model_validate(change_random(cells, '., -'))

        with pytest.raises(ValidationError):
            # Coluna na lista não está presente no modelo

            class MissingModel(ColumnMetadata):
                pass

            MissingModel.model_validate(cells)

        with pytest.raises(ValidationError):
            # Coluna está presente no module mas não foi declarado com tipo Coluna

            # column: list[str] = ['Lorem Ipsum dolor sit amet']
            class TypeErrorModel(ColumnMetadata):
                lorem_ipsum_dolor_sit_amet: str

            TypeErrorModel.model_validate(cells)

        assert MyModel.model_validate(cells)
        result_dict = MyModel.model_validate(cells).dict()
        assert len(result_dict) == len(columns)
        for metadata in result_dict.values():
            assert isinstance(metadata, dict)
            assert len(metadata) == 3
