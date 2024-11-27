from __future__ import annotations

from typing import Any, Mapping


def extract_from(mapping: Mapping, *keys: str) -> dict[str, Any]:
    new = {}
    for k in keys:
        if k in mapping and (v:=mapping[k]) is not None:
            new[k] = v
    return new
