from __future__ import annotations

from .validator import Validator

import sistema.spreadsheet as sheet

import re

from datetime import datetime
from string import whitespace
from typing import Never


class String(Validator):
    length: int | tuple[int, int] | None = None
    is_regular = True
    regex = re.compile(r'\S+(( |\S)+\S)?')
    qualified_type = sheet.STRING

    @classmethod
    def __validate(cls, value) -> str | Never:
        assert isinstance(value, str)
        assert cls.regex.match(value) is not None
        value = value.strip(whitespace)
        assert value != ''
        if cls.length is None:
            return value
        elif isinstance(cls.length, int):
            assert cls.length > 0
            assert len(value) == cls.length
            return value
        elif isinstance(cls.length, tuple):
            assert len(cls.length) == 2
            assert all(isinstance(v, int) for v in cls.length)
            assert all(v > 0 for v in cls.length)
            minlen, maxlen = cls.length
            assert minlen <= len(value) <= maxlen
            return value
        else:
            raise AssertionError("tipo inválido para propriedade 'length'")

    @classmethod
    def validate(cls, value) -> str | None:
        try:
            return cls.__validate(value)
        except AssertionError:
            return None


class IntegerString(String):
    length = None
    is_regular = True
    regex = re.compile(r'[0-9]+')
    qualified_type = sheet.STRING

    @classmethod
    def validate(cls, value):
        value = super().validate(value)
        if value is None:
            return None
        if cls.regex.fullmatch(value) is None:
            return None
        return value


class LetterString(String):
    pass


class Integer(String):
    pass


class Float(String):
    pass


class Date(String):
    length: int = len('dd/mm/yyyy')
    is_regular = True
    regex = re.compile(r'\d{2}\/\d{2}\/\d{4}')
    qualified_type = sheet.DATE
    format: str = '%d/%m/%Y'

    @classmethod
    def validate(cls, value):
        value = super().validate(value)
        if value is None:
            return None
        if cls.regex.fullmatch(value) is None:
            return None
        try:
            return datetime.strptime(value, cls.format).date()
        except ValueError:
            return None


class Boolean(String):
    pass


class Option(String):
    pass


class Enum(String):
    pass
