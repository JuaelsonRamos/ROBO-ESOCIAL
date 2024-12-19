from __future__ import annotations

from .Model import model

from src.types import IsRequired


@model
class Column:
    index: int
    original_text: str
    required: IsRequired
