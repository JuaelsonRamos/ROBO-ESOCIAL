from __future__ import annotations

from .Column import Column

from sistema.spreadsheet import QualifiedType, QualifiedValue, Requirement
from sistema.validators import Validator

from typing import Any

from pydantic import BaseModel, validator


class Cell(BaseModel, frozen=True, strict=True):
    index: int
    property_name: str
    required: Requirement
    is_empty: bool
    is_valid: bool
    is_arbitrary_string: bool
    qualified_type: QualifiedType
    validator: Validator
    original_value: str
    qualified_value: QualifiedValue
    column_metadata: Column

    @validator('column_metadata')
    def validate_column_metadata(cls, value: Any):
        assert isinstance(
            value, Column
        ), "'columns_metadata' deve ser um modelo derivado de 'ColumnMetadata'"
        return value

    @validator('validator')
    def validate_validator(cls, value: Any):
        assert isinstance(
            value, Validator
        ), "'validator' deve ser uma instância derivada de 'Validator'"
