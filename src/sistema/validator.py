from __future__ import annotations

from src.exc import ValidatorException
from src.sistema.models.Cell import Cell as CellModel
from src.sistema.models.Column import Column
from src.types import CellRichText, CellValue, CellValueType, EmptyValueType, IsRequired

import re
import string
import decimal
import hashlib
import inspect
import datetime
import itertools

from abc import abstractmethod
from re import Pattern
from typing import Any, Never, NoReturn, Self, Sequence, TypeVar, cast

from openpyxl.cell.cell import TIME_FORMATS, Cell
from unidecode import unidecode_expect_nonascii as unidecode


C = TypeVar('C', bound='ValidatorMeta')

EmptyValue = EmptyValueType()


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


re_spaces: Pattern[str] = re.compile(f'[{string.whitespace}]+')
re_punctuation: Pattern[str] = re.compile(f'[{string.punctuation}]+')
re_nonascii: Pattern[str] = re.compile(f'[^{string.printable}]+')


def hash_column_title(title: str) -> str:
    as_ascii = unidecode(title)
    normalized = as_ascii.strip(string.whitespace + string.punctuation).lower()
    normalized = re_spaces.sub(' ', normalized)
    normalized = re_punctuation.sub('*', normalized)
    normalized = re_nonascii.sub('', normalized)
    hashed = hashlib.md5(normalized.encode()).hexdigest().upper()
    return hashed


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


class Validator(metaclass=ValidatorMeta):
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
    value_type: type[CellValue]

    # set by __new__
    known_titles: tuple[str, ...]
    hashed_known_titles: tuple[str, ...]
    allow_empty: bool

    # set by __init__
    column: Column
    cell: Cell
    cell_index: int

    # static properties
    EmptyValue: EmptyValueType = EmptyValue
    """Unique, featureless object to represent an empty cell value."""

    @classmethod
    def new(
        cls: type[Self], /, known_titles: Sequence[str], allow_empty: bool = True
    ) -> type[Self]:
        """Create new class that holds primitive values for parsing and validation."""
        new_class = cls._make_creatable_class()
        instance = new_class.__new__(new_class, known_titles, allow_empty)
        return instance

    def __new__(
        cls: type[Self], /, known_titles: Sequence[str], allow_empty: bool
    ) -> Self | Never:
        if not cls._can_create_new:
            raise ValidatorException.RuntimeError
        cls._can_initialize = True
        instance = super().__new__(cls)
        instance.known_titles = tuple(known_titles)
        instance.hashed_known_titles = tuple(
            hash_column_title(title) for title in known_titles
        )
        instance.allow_empty = allow_empty
        return instance

    def with_data(self, /, column: Column, cell: Cell, cell_index: int) -> Self:
        """
        Creates new Validator and initializes it with provided data.

        The Validator returned by this function is a completely new instance!
        """
        new_instance = self.__new__(type(self), self.known_titles, self.allow_empty)
        new_instance.__init__(column, cell, cell_index)
        return new_instance

    def __init__(self, /, column: Column, cell: Cell, cell_index: int) -> None | Never:
        if not self._can_initialize:
            raise ValidatorException.RuntimeError
        self._can_call = True
        self.column = column
        self.cell = cell
        self.cell_index = cell_index

    def __call__(self) -> None | Never:
        if not self._can_call:
            raise ValidatorException.RuntimeError

    @abstractmethod
    def parse_value(self) -> CellValue | EmptyValueType | Never:
        """
        Parse arbitrary value to value of Validator's declared represented type.

        Implementation details:
        * If `self.allow_empty=False` then may raise `ValidatorException.EmptyValueError`.
        * If `ValidatorException.EmptyValueError` is raised, then value is not empty but
            is not valid either, so if `0` is invalid, then it is not empty, because it
            could be checked in the first place.
        * If an error is raised, the value that caused it does not needed to be included
            as error metadata, because if it is invalid, the way this system makes sense
            of real world data implies it is arbitrary, and **for now** there's no need
            to understand and no use case for values that are both invalid and non-empty.
        * `ValueError` and `TypeError` may be raised because of common python value
            conversion, like `int('non_digit')`. In these cases, a
            `ValidatorException.InvalidValueError` will be **raised from** the built-in
            python errors.

        :raises: ValidatorException.InvalidValueError
        :raises: ValidatorException.EmptyValueError
        :raises: ValueError
        :raises: TypeError
        """
        ...

    def is_value_valid(self) -> bool:
        """Parses value and returns `True` if no error occured and value is considered
        to have meaning in the context of this validator (didn't raise
        `InvalidValueError` or `EmptyValueError`).
        """
        try:
            self.parse_value()
        except (
            ValidatorException.InvalidValueError,
            ValidatorException.EmptyValueError,
        ):
            return False
        else:
            return True

    def to_dict(self) -> dict[str, Any]:
        """
        Parses value and return it as a `Cell` model-compliant dict.

        This method doesn't raise, thus, other's must be used to check validity of
        value.
        """
        # Both are False if self.parse_value() raises ValidatorException.InvalidValueError
        is_empty: bool = False
        is_valid: bool = False
        value: CellValue | EmptyValueType = self.EmptyValue
        parsed_value: CellValue | EmptyValueType = self.EmptyValue
        try:
            value = self.parse_value()
        except ValidatorException.EmptyValueError:
            is_empty = True
            is_valid = False
        except Exception:
            pass
        if value is self.EmptyValue:
            is_empty = True
            is_valid = self.allow_empty
        else:
            is_empty = False
            is_valid = True
            parsed_value = cast(CellValue, value)
        return {
            'index': self.cell_index,
            'required': IsRequired.from_cell(self.cell),
            'is_empty': is_empty,
            'is_valid': is_valid,
            'validator': self,
            'original_value': self.cell.value,
            'parsed_value': parsed_value,
            'column_metadata': self.column,
        }

    def to_model(self) -> CellModel:
        return CellModel(**self.to_dict())

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


class String(Validator):
    is_arbitraty_string = True
    cell_value_type = CellValueType.STRING
    value_type = str

    def to_string(self, *, bytes_encoding: str = 'utf-8') -> str:
        """
        Spreadsheet cell's value to valid string.

        Raises `ValidatorException.RuntimeError` if the spreadsheet's `Cell` object's
        value type is unknown, which should not be possible because those are provided
        by third-party libraries.

        :raises: ValidatorException.RuntimeError
        """
        value = self.cell.value
        valid_string: str = ''
        # NoneType
        if value is None:
            return ''
        # String
        elif isinstance(value, str):
            return value
        elif isinstance(value, bytes):
            valid_string = value.decode(encoding=bytes_encoding)
        # Numeric
        elif isinstance(value, (int, float)):
            valid_string = str(value)
        elif isinstance(value, decimal.Decimal):
            valid_string = decimal.getcontext().to_sci_string(value)

        elif isinstance(value, CellRichText):
            # TODO
            pass
        # Time
        elif isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            format = TIME_FORMATS[type(value)]
            valid_string = value.strftime(format)
        elif isinstance(value, datetime.timedelta):
            valid_string = str(value)
        # Boolean
        elif isinstance(value, bool):
            valid_string = str(value)
        # Other
        else:
            err = TypeError(f"type of {value} is unknown as a cell value's type")
            raise ValidatorException.RuntimeError(err) from err
        return valid_string

    def parse_value(self):
        parsed_value: str = ''
        try:
            parsed_value = self.to_string()
        except TypeError as err:
            raise ValidatorException.InvalidValueError(err) from err
        except Exception as err:
            raise ValidatorException.RuntimeError(err) from err
        # strip blank characters
        parsed_value = parsed_value.strip(string.whitespace)
        if parsed_value == '':
            if self.allow_empty:
                return self.EmptyValue
            raise ValidatorException.EmptyValueError
        # normalize encoding to ascii
        parsed_value = unidecode(parsed_value)
        # normalize case
        parsed_value = parsed_value.upper()
        return parsed_value


class LetterString(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str
    ...  # TODO: implement validator


class NumericString(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str
    ...  # TODO: implement validator


class IntegerString(NumericString):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str
    ...  # TODO: implement validator


class Float(NumericString):
    is_arbitraty_string = False
    cell_value_type = CellValueType.FLOAT
    value_type = float
    ...  # TODO: implement validator


class Integer(IntegerString):
    is_arbitraty_string = False
    cell_value_type = CellValueType.INT
    value_type = int
    ...  # TODO: implement validator


class Date(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.DATE
    value_type = datetime.date
    ...  # TODO: implement validator


class Option(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str
    ...  # TODO: implement validator


class Boolean(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.BOOL
    value_type = bool
    ...  # TODO: implement validator
