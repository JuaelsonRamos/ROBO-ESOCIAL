from __future__ import annotations

from .Model import model

from src.sistema.spreadsheet import Requirement


@model
class Column:
    i: int
    original_text: str
    property_name: str
    required: Requirement
