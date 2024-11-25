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
BOOL = 'bool'

QualifiedValue: TypeAlias = str | int | float | bool | date
QualifiedType: TypeAlias = Literal['string', 'int', 'float', 'bool', 'date']
