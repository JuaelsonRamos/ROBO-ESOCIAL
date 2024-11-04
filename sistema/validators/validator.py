from __future__ import annotations

from sistema.spreadsheet import QualifiedType, QualifiedValue

from abc import ABC, abstractclassmethod
from re import Pattern
from typing import Any


class Validator(ABC):
    is_regular: bool
    regex: Pattern[str] | None
    qualified_type: QualifiedType

    @abstractclassmethod
    def validate(self, raw_value: Any) -> QualifiedValue | None: ...
