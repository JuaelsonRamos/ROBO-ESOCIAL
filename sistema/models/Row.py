from __future__ import annotations

from sistema.models import ColumnMetadata
from sistema.spreadsheet import QualifiedType, QualifiedValue, Requirement
from sistema.validators import Validator

from pydantic import BaseModel


class Row(BaseModel, frozen=True, strict=True):
    index: int
    property_name: str
    required: Requirement
    is_opcional: bool
    is_empty: bool
    qualified_type: QualifiedType
    validator_class: Validator
    original_value: str
    qualified_value: QualifiedValue
    columns_metadata: ColumnMetadata
