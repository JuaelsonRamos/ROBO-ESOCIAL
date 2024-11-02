from __future__ import annotations

from .ColumnMetadata import ColumnMetadata
from .Row import Row

import sistema.spreadsheet as sheet

from sistema.validators import Validator
from utils import isiterable

from typing import Iterable, Never, get_type_hints

from openpyxl.cell import Cell
from pydantic import BaseModel, model_validator


class RowData(BaseModel, frozen=True, strict=True):
    @model_validator(mode='before')
    @classmethod
    def _input(
        self, metadata: ColumnMetadata, data: Iterable[Cell]
    ) -> dict[str, Row] | Never:
        assert isiterable(data)
        assert all(isinstance(it, Cell) for it in data)
        assert isinstance(metadata, ColumnMetadata)
        columns, fields = metadata.dict(), get_type_hints(self)
        assert len(fields) == len(data)
        assert len(fields) == len(columns)
        assert all(prop_here in columns for prop_here in fields.keys())
        assert all(issubclass(T, Validator) for T in fields.values())
        validated = {}
        for prop, cell in zip(fields.keys(), data):
            col = columns['prop']
            validator: Validator = fields[prop]
            value = validator.validate(cell.value)
            validated[prop] = {
                'index': col['index'],
                'property_name': prop,
                'required': col['required'],
                'is_opcional': col['required'] == sheet.OPCIONAL,
                'is_empty': value is None,
                'qualified_type': validator.qualified_type,
                'validator_class': validator,
                'original_value': cell.value,
                'qualified_value': value,
                'columns_metadata': metadata,
            }
        return validated
