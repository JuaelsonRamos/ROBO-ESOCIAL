from __future__ import annotations

from utils import EmptyString

import io
import re
import string

from tempfile import NamedTemporaryFile

from openpyxl import Workbook
from unidecode import unidecode_expect_nonascii


def as_bytes(book: Workbook) -> bytes:
    with NamedTemporaryFile() as tmp:
        book.save(tmp)
        return tmp.read()


def normalize_column_title(value: str, is_unicode: bool = False) -> str:
    value = value.strip(string.whitespace)
    if value == '':
        raise EmptyString
    if is_unicode:
        value = unidecode_expect_nonascii(value)
    value = value.lower()
    replace = {'$': 's'}
    with io.StringIO() as property_name:
        for ch in value:
            property_name.write(replace.get(ch, ch))
        value = property_name.getvalue()
    value = re.sub(r'[^a-z0-9]+', '_', value).strip('_')
    if value == '':
        raise EmptyString
    return value
