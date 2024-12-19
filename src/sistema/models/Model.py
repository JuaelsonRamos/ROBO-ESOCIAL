from __future__ import annotations

import inspect

from dataclasses import Field, asdict, astuple, dataclass, fields, replace
from typing import Any, Self, TypeVar, cast, dataclass_transform

from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema
from pydantic_core.core_schema import DataclassSchema, SimpleSerSchema


_adapters_registry: dict[int, TypeAdapter] = {}


@dataclass(frozen=True, slots=True)
class ModelType:
    def type_adapter(self) -> TypeAdapter: ...

    def astuple(self) -> tuple[Any, ...]: ...

    def asdict(self) -> dict[str, Any]: ...

    def replace(self, /, **changes: Any) -> Self: ...

    def fields(self) -> tuple[Field[Any]]: ...

    def __getitem__(self, name: str, /) -> Any: ...

    @classmethod
    def __get_pydantic_core_schema__(
        cls: type[Any], source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema: ...


_Model = TypeVar('_Model', bound=type[Any])


@dataclass_transform(kw_only_default=False, frozen_default=True)
def model(cls: type[Any]) -> type[ModelType]:
    """
    Class decorator that allows both metaclass-like transformation and decorator syntax.

    The central goal is to not use pydantic models directly in favor of standard python
    objects (because I'm too smooth brained to learn pydantic for now) while providing
    an attached method for retrieving pydantic type adapters.
    """

    _dataclass_factory = dataclass(frozen=True, slots=True)

    @classmethod
    def _generic_get_pydantic_core_schema(
        cls: _Model, source_type: _Model, handler: GetCoreSchemaHandler
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

    def _get_type_adapter(self) -> TypeAdapter:
        global _adapters_registry
        return _adapters_registry[self._adapter_index]

    def _astuple(self):
        return astuple(self)

    def _asdict(self):
        return asdict(self)

    def _replace(self, /, **changes):
        """Return new Model with modified fields denoted by `**changes`."""
        return replace(self, **changes)

    def _fields(self):
        return fields(self)

    def _dunder_getitem(self, name: str, /) -> Any:
        try:
            return getattr(self, name)
        except AttributeError as err:
            raise IndexError(err)

    i = len(_adapters_registry)
    _patched_namespace = dict(
        _adapter_index=i,
        type_adapter=_get_type_adapter,
        astuple=_astuple,
        asdict=_asdict,
        replace=_replace,
        fields=_fields,
        __getitem__=_dunder_getitem,
        __get_pydantic_core_schema__=_generic_get_pydantic_core_schema,
    )
    _original_namespace = vars(cls).copy()
    _metaclass = type(cls)

    _class = type.__new__(_metaclass, cls.__name__, cls.__bases__, _original_namespace)

    # Based on: https://gist.github.com/floer32/a928b801ca5c7705e94e
    # Binding the function to the class as methods instead of simple function references.
    for as_name, func in _patched_namespace.items():
        if inspect.ismethoddescriptor(func) or inspect.isfunction(func):
            setattr(_class, as_name, func.__get__(_class, _metaclass))

    _as_dataclass = _dataclass_factory(_class)

    _adapters_registry[i] = TypeAdapter(_as_dataclass)

    return cast(type[ModelType], _as_dataclass)
