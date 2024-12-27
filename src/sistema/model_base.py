from __future__ import annotations

from dataclasses import asdict, astuple, dataclass, fields, replace
from typing import Any, cast, dataclass_transform

from pydantic import ConfigDict, GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema
from pydantic_core.core_schema import DataclassSchema, SimpleSerSchema


@dataclass_transform(frozen_default=True)
def model_dataclass(func):
    return dataclass(init=True, frozen=True, slots=True, unsafe_hash=True)(func)


class ModelMeta(type):
    _adapters: dict[type, TypeAdapter] = {}

    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> ModelMeta:
        _class = super(ModelMeta, cls).__new__(cls, name, bases, namespace)
        return _class

    def _get_type_adapter(cls):
        if cls not in cls._adapters:
            cls._adapters[cls] = TypeAdapter(cls, config=ConfigDict(strict=False))
        return cls._adapters[cls]


@model_dataclass
class Model(metaclass=ModelMeta):
    @classmethod
    def type_adapter(cls) -> TypeAdapter:
        return cls._get_type_adapter()

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
