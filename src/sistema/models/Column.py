from __future__ import annotations

from .Model import Model

from src.sistema.spreadsheet import Requirement

from typing import NamedTuple


class Column(NamedTuple, Model):  # type: ignore
    i: int
    original_text: str
    property_name: str
    required: Requirement
