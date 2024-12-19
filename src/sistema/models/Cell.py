from __future__ import annotations

from .Column import Column
from .Model import model

from src.sistema.validators import Validator
from src.types import CellValue, IsRequired


@model
class Cell:
    index: int
    required: IsRequired
    is_empty: bool
    is_valid: bool
    validator: Validator
    original_value: str | None
    parsed_value: CellValue | None
    column_metadata: Column
