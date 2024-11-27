from __future__ import annotations

from .schema import schema
from ..parser import Parser


class Modelo1(Parser):
    def _define_schema(self):
        super()._define_schema()
        self._schema = schema
