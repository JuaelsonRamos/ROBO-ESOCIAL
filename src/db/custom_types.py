from __future__ import annotations

import string

from datetime import datetime, tzinfo
from typing import Any, SupportsIndex
from urllib.parse import urlparse

from sqlalchemy import TEXT, TypeDecorator
from sqlalchemy.engine.interfaces import Dialect


# pyright: reportArgumentType=false

RowDataType = int | float | str | bytes | bool | datetime


class timestamp(datetime):
    def __new__(
        cls,
        year: SupportsIndex,
        month: SupportsIndex,
        day: SupportsIndex,
        hour: SupportsIndex = ...,
        minute: SupportsIndex = ...,
        second: SupportsIndex = ...,
        microsecond: SupportsIndex = ...,
        tzinfo: tzinfo | None = ...,
        *,
        fold: int = ...,
    ) -> datetime:
        return datetime.__new__(
            datetime,
            year,
            month,
            day,
            hour,
            minute,
            second,
            microsecond,
            tzinfo,
            fold=fold,
        )


class Url(TypeDecorator):
    impl = TEXT

    def process_literal_param(self, value: Any | None, dialect: Dialect) -> str:
        if value is None:
            return 'NULL'
        if not isinstance(value, str):
            raise TypeError(f'{type(value).__name__=} expected str or None')
        formatted = value.strip(string.whitespace)
        url = urlparse(formatted)
        if url.scheme == '' or url.netloc == '' or '.' not in url.netloc:
            raise ValueError(f'{url=} scheme or netloc invalid')
        return f"'{url.geturl()}'"  # literal string is single-quoted

    def process_result_value(self, value: Any | None, dialect: Dialect) -> Any | None:
        return urlparse(value) if value is not None else None
