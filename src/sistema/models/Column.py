from __future__ import annotations

from .Model import Model

from src.sistema.spreadsheet import Requirement

from dataclasses import dataclass


@dataclass
class Column(Model):
    i: int
    original_text: str
    property_name: str
    required: Requirement
