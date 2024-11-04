from __future__ import annotations

from .ColumnMetadata import ColumnMetadata

from sistema.spreadsheet import QualifiedType, QualifiedValue, Requirement

from typing import Any, Generic, T

from pydantic import BaseModel, validator


class Row(
    BaseModel,
    Generic[T],
    frozen=True,
    strict=True,
    arbitrary_types_allowed=True,
):
    index: int
    property_name: str
    required: Requirement
    is_opcional: bool
    is_empty: bool
    qualified_type: QualifiedType
    validator_class: type[T]
    original_value: str
    qualified_value: QualifiedValue
    columns_metadata: ColumnMetadata

    @validator('columns_metadata')
    def validate_columns_metadata(cls, value: Any):
        assert issubclass(
            type(value), ColumnMetadata
        ), "'columns_metadata' deve ser um modelo derivado de 'ColumnMetadata'"
        return value
