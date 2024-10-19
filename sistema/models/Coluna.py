from __future__ import annotations

from enum import StrEnum, auto

from pydantic import BaseModel


class Required(StrEnum):
    MANDATORY = auto()
    OPCIONAL = auto()
    CASE_SPECIFIC = auto()


class Coluna(BaseModel):
    index: int
    original_text: str
    required: Required
