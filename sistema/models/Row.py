from __future__ import annotations

from sistema.models import ColumnMetadata
from sistema.spreadsheet import QualifiedType, QualifiedValue, Requirement

from typing import Generic, T

from pydantic import BaseModel


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
