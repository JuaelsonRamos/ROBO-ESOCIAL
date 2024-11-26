from __future__ import annotations

from .Column import Column

from src.sistema.spreadsheet import QualifiedType, QualifiedValue, Requirement
from src.sistema.validators import Validator

from typing import TypeVar

from pydantic import BaseModel, field_validator


T = TypeVar('T')


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
    qualified_value: QualifiedValue | None
    column_metadata: Column

    @field_validator('column_metadata')
    def validate_column_metadata(cls, value: T) -> T:
        assert isinstance(
            value, Column
        ), "'columns_metadata' deve ser um modelo derivado de 'Column'"
        return value  # type: ignore

    @field_validator('validator')
    def validate_validator(cls, value: T) -> T:
        assert isinstance(
            value, Validator
        ), "'validator' deve ser uma instância derivada de 'Validator'"
        return value  # type: ignore
