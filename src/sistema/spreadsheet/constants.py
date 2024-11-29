from __future__ import annotations

from datetime import date
from typing import Final, Literal, TypeAlias


REQUIRED: Final = 'required'
OPCIONAL: Final = 'opcional'
MAYBE: Final = 'maybe'

Requirement: TypeAlias = Literal['required', 'opcional', 'maybe']

STRING: Final = 'string'
INT: Final = 'int'
FLOAT: Final = 'float'
DATE: Final = 'date'
BOOL: Final = 'bool'

QualifiedValue: TypeAlias = str | int | float | bool | date
QualifiedType: TypeAlias = Literal['string', 'int', 'float', 'bool', 'date']
