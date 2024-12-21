from __future__ import annotations

from .Column import Column
from .Model import model

from src.sistema.validators import Validator
from src.types import CellValue, EmptyValueType, IsRequired, OpenpyxlCell


@model
class Cell:
    index: int
    required: IsRequired
    is_empty: bool
    is_valid: bool
    validator: Validator
    original_value: OpenpyxlCell.KnownTypes
    parsed_value: CellValue | EmptyValueType
    column_metadata: Column
