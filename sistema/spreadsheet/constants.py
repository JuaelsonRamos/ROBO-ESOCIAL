from __future__ import annotations

from typing import Literal, TypeAlias


REQUIRED = 'required'
OPCIONAL = 'opcional'
MAYBE = 'maybe'

Requirement: TypeAlias = Literal[REQUIRED, OPCIONAL, MAYBE]
