from __future__ import annotations

from datetime import date
from typing import Literal, TypeAlias


REQUIRED = 'required'
OPCIONAL = 'opcional'
MAYBE = 'maybe'

Requirement: TypeAlias = Literal['required', 'opcional', 'maybe']

STRING = 'string'
INT = 'int'
FLOAT = 'float'
DATE = 'date'

QualifiedValue: TypeAlias = str | int | float | date
QualifiedType: TypeAlias = Literal['string', 'int', 'float', 'date']
