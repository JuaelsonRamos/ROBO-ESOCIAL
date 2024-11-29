from __future__ import annotations

from .Column import Column
from .Model import Model

from src.sistema.spreadsheet import QualifiedType, QualifiedValue, Requirement
from src.sistema.validators import Validator

from typing import NamedTuple


class Cell(NamedTuple, Model):  # type: ignore
    i: int
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
