from __future__ import annotations

from tempfile import NamedTemporaryFile

from openpyxl import Workbook


def as_bytes(book: Workbook) -> bytes:
    with NamedTemporaryFile() as tmp:
        book.save(tmp)
        return tmp.read()
