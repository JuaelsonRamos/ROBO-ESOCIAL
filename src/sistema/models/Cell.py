from __future__ import annotations

from .Column import Column
from .Model import model

from src.sistema.validators import Validator
from src.types import IsRequired, T_CellValue

from typing import Any, Generic


@model
class Cell(Generic[T_CellValue]):
    index: int
    required: IsRequired
    is_empty: bool
    is_valid: bool
    validator: Validator
    original_value: Any
    parsed_value: T_CellValue | None
    column_metadata: Column
