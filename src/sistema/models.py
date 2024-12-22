from __future__ import annotations

from src.sistema.validator import Validator
from src.types import CellValue, EmptyValueType, IsRequired, OpenpyxlCell

import itertools

from dataclasses import asdict, astuple, dataclass, fields, replace
from typing import Any, cast, dataclass_transform

from pydantic import ConfigDict, GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema
from pydantic_core.core_schema import DataclassSchema, SimpleSerSchema


@dataclass_transform(frozen_default=True)
class ModelMeta(type):
    _adapters: list[TypeAdapter] = []
    _get_class_index = itertools.count(-1, 1).__next__
    _dataclass_factory = dataclass(init=True, frozen=True, slots=True, unsafe_hash=True)
    _current_class_index: int

    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> ModelMeta:
        i = cls._get_class_index()
        namespace['_current_class_index'] = i
        _class = super(ModelMeta, cls).__new__(cls, name, bases, namespace)
        _class = cls._dataclass_factory(_class)
        if i < 0:
            # Exclude first inheritance (Model class)
            adapter = TypeAdapter(_class, config=ConfigDict(strict=False))
            cls._adapters.append(adapter)
        return cast('ModelMeta', _class)


class Model(metaclass=ModelMeta):
    @classmethod
    def type_adapter(cls) -> TypeAdapter:
        if cls._current_class_index < 0:
            raise RuntimeError('no TypeAdapter for base Model class')
        return cls._adapters[cls._current_class_index]

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[Model], handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        # schemas are just dicts filled with metadata
        schema = cast(dict[str, Any], handler(source_type))
        schema_config_patch = dict(
            cls_name=cls.__name__,
            revalidate_instances='subclass-instances',
            strict=False,
            frozen=True,
            slots=True,
            serialization=SimpleSerSchema(type='json'),
        )
        schema.update(schema_config_patch)
        return cast(DataclassSchema, schema)

    def astuple(self):
        return astuple(self)  # type: ignore

    def asdict(self):
        return asdict(self)  # type: ignore

    def replace(self, /, **changes):
        """Return new Model with modified fields denoted by `**changes`."""
        return replace(self, **changes)  # type: ignore

    def fields(self):
        return fields(self)  # type: ignore

    def __getitem__(self, name: str, /) -> Any:
        try:
            return getattr(self, name)
        except AttributeError as err:
            raise IndexError(err)


class Column(Model):
    index: int
    original_text: str
    required: IsRequired
    validator: Validator


class Cell(Model):
    index: int
    required: IsRequired
    is_empty: bool
    is_valid: bool
    validator: Validator
    original_value: OpenpyxlCell.KnownTypes
    parsed_value: CellValue | EmptyValueType
    column_metadata: Column
