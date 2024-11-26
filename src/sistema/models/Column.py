from __future__ import annotations

from src.sistema.spreadsheet import Requirement

from pydantic import BaseModel


class Column(BaseModel):
    index: int
    original_text: str
    property_name: str
    required: Requirement
