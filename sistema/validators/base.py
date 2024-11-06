from __future__ import annotations

from .validator import Validator

import sistema.spreadsheet as sheet

import re

from datetime import datetime
from string import whitespace
from typing import Any, Never

from unidecode import unidecode_expect_nonascii


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

    allow_zero: bool = True

    @classmethod
    def validate(cls, value):
        value = super().validate(value)
        if value is None:
            return None
        if cls.regex.fullmatch(value) is None:
            return None
        if not cls.allow_zero and int(value) == 0:
            return None
        return value


class LetterString(String):
    length = None
    is_regular = False
    regex = None
    qualified_type = sheet.STRING

    __ascii = re.compile(r'[a-zA-Z ]+')

    @classmethod
    def validate(cls, value):
        value = super().validate(value)
        if value is None:
            return None
        if cls.__ascii.fullmatch(unidecode_expect_nonascii(value)) is None:
            return None
        return value


class Integer(IntegerString):
    @classmethod
    def validate(cls, value) -> int | None:
        value = super().validate(value)
        if value is None:
            return None
        return int(value)


class Float(String):
    @classmethod
    def validate(cls, value) -> float | None:
        value = super().validate(value)
        if value is None:
            return None
        return float(value)


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
    falsy: tuple[str] = tuple()
    truthy: tuple[str] = tuple()
    case_sensitive: bool = False
    unicode_sensitive: bool = False

    @classmethod
    def validate(cls, value) -> bool | None:
        value = super().validate(value)
        if value is None:
            return None
        if len(cls.falsy) == len(cls.truthy) == 0:
            return None
        falsy, truthy = cls.falsy, cls.truthy
        if not cls.unicode_sensitive:
            value = unidecode_expect_nonascii(value)
            falsy = tuple(unidecode_expect_nonascii(v) for v in falsy)
            truthy = tuple(unidecode_expect_nonascii(v) for v in truthy)
        if not cls.case_sensitive:
            value = value.lower()
            falsy = tuple(v.lower() for v in falsy)
            truthy = tuple(v.lower() for v in truthy)
        if value in truthy:
            return True
        if value in falsy:
            return False
        return None


class Option(String):
    options: tuple[str] = tuple()
    case_sensitive: bool = False
    unicode_sensitive: bool = False

    @classmethod
    def validate(cls, value) -> str | None:
        value = super().validate(value)
        if value is None:
            return None
        if len(cls.options) == 0:
            return None
        options = cls.options
        if not cls.unicode_sensitive:
            value = unidecode_expect_nonascii(value)
            options = tuple(unidecode_expect_nonascii(v) for v in options)
        if not cls.case_sensitive:
            value = value.lower()
            options = tuple(v.lower() for v in options)
        try:
            return options[options.index(value)]
        except ValueError:
            # tuple.index raises ValueError, no need to consider it may be out of bounds
            return None


class Enum(String):
    enum: dict[str, Any] = {}
    case_sensitive: bool = False
    unicode_sensitive: bool = False

    @classmethod
    def validate(cls, value) -> tuple[str, Any] | None:
        value = super().validate(value)
        if value is None:
            return None
        if len(cls.enum) == 0:
            return None
        enum = cls.enum
        if not cls.unicode_sensitive:
            value = unidecode_expect_nonascii(value)
            enum = {unidecode_expect_nonascii(k): v for k, v in enum.items()}
        if not cls.case_sensitive:
            value = value.lower()
            enum = {k.lower(): v for k, v in enum.items()}
        return (value, enum[value]) if value in enum else None
