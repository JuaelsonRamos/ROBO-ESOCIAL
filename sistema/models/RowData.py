from __future__ import annotations

from .ColumnMetadata import ColumnMetadata
from .Row import Row

import sistema.spreadsheet as sheet

from sistema.validators import Validator
from utils import isiterable

import inspect

from typing import Generic, Iterable, Never, get_type_hints

from openpyxl.cell import Cell
from pydantic import BaseModel, model_validator


class RowData(BaseModel, frozen=True, strict=True):
    @model_validator(mode='before')
    @classmethod
    def _input(
        self, obj: tuple[ColumnMetadata, Iterable[Cell]]
    ) -> dict[str, Row] | Never:
        metadata, data = obj
        assert isiterable(data)
        assert all(isinstance(it, Cell) for it in data)
        assert isinstance(metadata, ColumnMetadata)
        columns, fields = metadata.dict(), get_type_hints(self)
        assert len(fields) == len(data)
        assert len(fields) == len(columns)
        for prop_here, T in fields.items():
            assert prop_here in columns
            assert issubclass(T, Row) and issubclass(T, Generic)
            generic_meta = T.__pydantic_generic_metadata__
            assert generic_meta['origin'] is Row
            assert len(generic_meta['args']) == 1
            type_arg = generic_meta['args'][0]
            assert inspect.isclass(type_arg)
            assert issubclass(type_arg, Validator)
        validated = {}
        for prop, cell in zip(fields.keys(), data):
            col = columns[prop]
            type_metadata = fields[prop].__pydantic_generic_metadata__
            validator: Validator = type_metadata['args'][0]
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
