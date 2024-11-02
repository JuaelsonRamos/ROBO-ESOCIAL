from __future__ import annotations

from sistema.spreadsheet import QualifiedType, QualifiedValue

from abc import ABC, abstractmethod
from re import Pattern
from typing import Generic, TypeVar


T = TypeVar('T', QualifiedValue)


class Validator(ABC, Generic[T]):
    is_regular: bool
    regex: Pattern[str] | None
    qualified_type: QualifiedType

    @abstractmethod
    def validate(self, raw_value: str) -> T | None: ...
