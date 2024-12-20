from __future__ import annotations

from src.exc import ValidatorException
from src.sistema.models.Cell import Cell as CellModel
from src.sistema.models.Column import Column
from src.sistema.spreadsheet import Fill
from src.types import CellValueType, IsRequired

import re
import string
import hashlib
import inspect
import itertools

from abc import abstractmethod
from re import Pattern
from typing import Any, Generic, Iterable, Never, NoReturn, Self, Sequence, TypeVar

from openpyxl.cell.cell import Cell
from unidecode import unidecode_expect_nonascii as unidecode


def get_requirement(cell: Cell) -> IsRequired:
    if cell.fill == Fill.RED:
        return IsRequired.REQUIRED
    if cell.fill == Fill.BLUE:
        return IsRequired.UNCERTAIN
    return IsRequired.OPTIONAL


C = TypeVar('C', bound='ValidatorMeta')
V = TypeVar('V', bound=Any)


def _make_slots_from(cls: type, namespace: dict[str, Any]) -> tuple[str, ...]:
    """Create __slots__ tuple."""
    all_values: set[str] = set(
        itertools.chain(
            getattr(cls, '__slots__', ()),
            inspect.get_annotations(cls).keys(),
            namespace.get('__slots__', ()),
        )
    )
    for name in ('__slots__', ''):
        try:
            all_values.remove(name)
        except KeyError:
            continue
    return tuple(all_values)


class ValidatorMeta(type):
    """
    Prevent class from being called until both __new__ and __init__ has been ran once,
    enforcing the use of .new() to create a new `Validator` (class variable) and
    .with_data() create (another) an initialized instance `Validator` in place of
    __init__.

    For concerns about hashing, lookup the methods __hash__ and .meta_hash() for
    documentation.
    """

    __slots__ = ()

    _hash: int
    """Cached hash for comparisons."""

    _meta_hash: int
    """Auto generated hash of subsequent class variables."""

    _can_call: bool = False
    """Wheter __call__ can be called."""

    _can_create_new: bool = False
    """Wheter __new__ can be called."""

    _can_initialize: bool = False
    """Wheter __init__ can be called."""

    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> ValidatorMeta:
        # Build original class object
        namespace['__slots__'] = _make_slots_from(cls, namespace)
        module_class_symbol = super(ValidatorMeta, cls).__new__(
            cls, name, bases, namespace
        )
        module_class_symbol._hash = super(ValidatorMeta, module_class_symbol).__hash__()
        return module_class_symbol

    def _make_creatable_class(cls: C) -> C:
        """Create brand new class with relevant flag so that __new__ can be called."""
        # Build class instance object
        namespace: dict[str, Any] = vars(cls).copy()
        namespace['__slots__'] = _make_slots_from(cls, namespace)
        # set flag
        namespace['_can_create_new'] = True
        new_class = super(ValidatorMeta, cls).__new__(
            cls, cls.__name__, cls.__bases__, namespace
        )
        # set meta-hash (see __hash__ docstring)
        new_class._meta_hash = super(ValidatorMeta, new_class).__hash__()
        return new_class

    def __call__(self) -> NoReturn:
        # Do not allow class variable to be called and created.
        # Blocks type.__call__ meaning `class()` won't call type.__new__ nor type.__init__
        raise ValidatorException.RuntimeError


class Validator(Generic[V], metaclass=ValidatorMeta):
    # fmt: off
    """
    Validation and parsing agent for spreadsheet cells.

    A `Validator` object must be created using the `.new()` method, which returns a new
    `Validator` class. This ensures every validator is unique both as an object and for
    the given initial metadata passed to `.new()`.

    Then the `Validator` object must be initialized with the method `.with_data()` which
    returns an instance of another `Validator` object created on the spot. This ensures
    case-specific metadata can be generated and calculated per spreadsheet, per cell.

    The expected pattern is the following:
    ```python
    # validator.py
    class Validator: ...                         # class 1
    # schema.py
    field_validator = Validator.new(...)         # class 2, instance 1
    # parsing.py
    field_data = field_validator.with_data(...)  # class 3, instance 2
    field_data.is_arbitraty_string  # generic
    field_data.cell_value_type      # generic
    field_data.value_type           # generic
    field_data.parse_value()     # case specific
    field_data.is_value_valid()  # case specific
    field_data.to_dict()         # case specific
    field_data.to_model()        # case specific
    ```

    To create a new instance of `Validator`, call `.new()`, then, call `.with_data()` to
    initialize the object. Calling both __new__ and __init__ directly won't work, they
    are locked up the `Validator` base class mechanisms. The .new() and .with_data()
    return new instances of the class.

    A `Validator` instance will only be usable upon initialization, that is, calling
    `.with_data()`.
    """
    # fmt: on

    # __slots__ will be automatically generated, this is a dummy symbol
    __slots__: tuple[str, ...]

    # META:
    _hash: int
    _meta_hash: int
    _can_call: bool
    _can_create_new: bool
    _can_initialize: bool

    # NON-META:
    is_arbitraty_string: bool
    cell_value_type: CellValueType
    value_type: type

    re_spaces: Pattern[str] = re.compile(f'[{string.whitespace}]+')
    re_punctuation: Pattern[str] = re.compile(f'[{string.punctuation}]+')
    re_nonascii: Pattern[str] = re.compile(f'[^{string.printable}]+')

    @classmethod
    def new(cls: type[Self]) -> type[Self]:
        """Create new class that holds primitive values for parsing and validation."""
        new_class = cls._make_creatable_class()
        instance = new_class.__new__(new_class)
        return instance

    def __new__(cls: type[Self]) -> Self | Never:
        if not cls._can_create_new:
            raise ValidatorException.RuntimeError
        cls._can_initialize = True
        instance = super().__new__(cls)
        return instance

    def with_data(self, /, known_titles: Sequence[str]) -> Self:
        """
        Creates new Validator and initializes it with provided data.

        The Validator returned by this function is a completely new instance!
        """
        new_instance = self.__new__(type(self))
        new_instance.__init__(known_titles)
        return new_instance

    def __init__(self, /, known_titles: Sequence[str]) -> None | Never:
        if not self._can_initialize:
            raise ValidatorException.RuntimeError
        self._can_call = True
        self.title_hashes = self._hash_nonascii_string(known_titles)

    def __call__(self) -> None | Never:
        if not self._can_call:
            raise ValidatorException.RuntimeError

    def _hash_nonascii_string(self, strings: Iterable[str]) -> Iterable[str]:
        _result = []
        for some_str in strings:
            as_ascii = unidecode(some_str)
            normalized = as_ascii.strip(string.whitespace + string.punctuation).lower()
            normalized = self.re_spaces.sub(' ', normalized)
            normalized = self.re_punctuation.sub('*', normalized)
            normalized = self.re_nonascii.sub('', normalized)
            hashed = hashlib.md5(normalized.encode()).hexdigest().upper()
            _result.append(hashed)
        return tuple(_result)

    @abstractmethod
    def parse_value(self, value: Any) -> V | Never:
        """
        Parse arbitrary value to value of Validator's declared represented type.

        :raises: ValidatorException.InvalidValueError
        :raises: ValidatorException.EmptyValueError
        :raises: ValueError
        :raises: TypeError
        """
        ...

    def is_value_valid(self, value: Any) -> bool:
        """Parses value and returns `True` if no error occured and value is considered
        to have meaning in the context of this validator (didn't raise
        `InvalidValueError` or `EmptyValueError`).
        """
        try:
            self.parse_value(value)
        except (
            ValidatorException.InvalidValueError,
            ValidatorException.EmptyValueError,
            ValueError,
            TypeError,
        ):
            return False
        else:
            return True

    def to_dict(self, /, column: Column, cell: Cell, cell_index: int) -> dict[str, Any]:
        return {
            'index': cell_index,
            'required': get_requirement(cell),
            'validator': self,
            'original_value': cell.value,
            'column_metadata': column,
        }

    def to_model(self, /, column: Column, cell: Cell, cell_index: int) -> CellModel:
        return CellModel(**self.to_dict(column, cell, cell_index))

    @classmethod
    def meta_hash(cls) -> int:
        return cls._meta_hash

    @classmethod
    def __hash__(cls) -> int:
        """
        Return hash generated upon loading of module and creation of class variable.

        This hash represents the hash of the original symbol importable from the module.
        Instances of this class contain different hashes due to them being interely new
        classes. Their individual auto-generatoed hash can be accessed using the
        .meta_hash() method. This workaround exists to compare classes in case a
        __hash__ method is not implemented. Feel free to implement a __hash__ method, as
        it is supposed to override the automatically generated hash by design.
        """
        return cls._hash


class String(Validator): ...


class LetterString(String): ...


class NumericString(String): ...


class IntegerString(NumericString): ...


class Float(NumericString): ...


class Integer(IntegerString): ...


class Date(String): ...


class Option(String): ...


class Boolean(String): ...
