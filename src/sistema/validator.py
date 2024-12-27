from __future__ import annotations

from src.exc import ValidatorException
from src.sistema.model_base import Model
from src.types import (
    CellRichText,
    CellValue,
    CellValueType,
    EmptyValueType,
    IsRequired,
    OpenpyxlCell,
)

import re
import math
import string
import decimal
import hashlib
import inspect
import itertools

from abc import abstractmethod
from datetime import date, datetime, time, timedelta, timezone
from re import Pattern
from typing import Any, Never, NoReturn, Self, Sequence, TypeVar, cast

from openpyxl.cell.cell import TIME_FORMATS, Cell
from typing_extensions import TypeIs
from unidecode import unidecode_expect_nonascii as unidecode


# region DATA MODELS


class ColumnModel(Model):
    index: int
    original_text: str
    required: IsRequired
    validator: Validator


class CellModel(Model):
    index: int
    required: IsRequired
    is_empty: bool
    is_valid: bool
    validator: Validator
    original_value: OpenpyxlCell.KnownTypes
    parsed_value: CellValue | EmptyValueType
    column_metadata: ColumnModel


# endregion

# region VALIDATOR METACLASS

C = TypeVar('C', bound='ValidatorMeta')


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


_escaped_puctuation = '\\' + '\\'.join(string.punctuation)
re_spaces: Pattern[str] = re.compile(f'[{string.whitespace}]+')
re_punctuation: Pattern[str] = re.compile(f'[{_escaped_puctuation}]+')
re_nonascii: Pattern[str] = re.compile(f'[^{string.printable}]+')


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


# endregion

# region VALIDATOR BASE CLASS


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
    column: ColumnModel
    cell: Cell
    cell_index: int

    # static properties
    EmptyValue: EmptyValueType = EmptyValueType()
    """Unique, featureless object to represent an empty cell value."""

    @classmethod
    def is_empty(cls, value: Any) -> TypeIs[EmptyValueType]:
        return isinstance(value, EmptyValueType) and value is cls.EmptyValue

    @staticmethod
    def hash_column_title(title: str) -> str:
        as_ascii = unidecode(title)
        normalized = as_ascii.strip(string.whitespace + string.punctuation).lower()
        normalized = re_spaces.sub(' ', normalized)
        normalized = re_punctuation.sub('*', normalized)
        normalized = re_nonascii.sub('', normalized)
        hashed = hashlib.md5(normalized.encode()).hexdigest().upper()
        return hashed

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
            cls.hash_column_title(title) for title in known_titles
        )
        instance.allow_empty = allow_empty
        return instance

    def with_data(self, /, column: ColumnModel, cell: Cell) -> Self:
        """
        Creates new Validator and initializes it with provided data.

        The Validator returned by this function is a completely new instance!
        """
        new_instance = self.__new__(type(self), self.known_titles, self.allow_empty)
        new_instance.__init__(column, cell)
        return new_instance

    def __init__(self, /, column: ColumnModel, cell: Cell) -> None | Never:
        if not self._can_initialize:
            raise ValidatorException.RuntimeError
        self._can_call = True
        self.column = column
        self.cell = cell
        self.cell_index = column.index

    def __call__(self) -> None | Never:
        if not self._can_call:
            raise ValidatorException.RuntimeError

    @abstractmethod
    @classmethod
    def matches(cls, column_cell: Cell) -> bool: ...

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


# endregion

# region BASE STRING VALIDATOR AND PARSER


def cell_value_to_string(value: Any, *, bytes_encoding: str = 'utf-8') -> str:
    """
    Spreadsheet cell's value to valid string.

    Raises `ValidatorException.RuntimeError` if the spreadsheet's `Cell` object's
    value type is unknown, which should not be possible because those are provided
    by third-party libraries.

    :raises: ValidatorException.RuntimeError
    """
    valid_string: str = ''
    # NoneType
    if value is None:
        return ''
    # String
    elif isinstance(value, str):
        return value
    elif isinstance(value, bytes):
        valid_string = value.decode(encoding=bytes_encoding)
    elif isinstance(value, CellRichText):
        # TODO
        pass
    # Numeric
    elif isinstance(value, (int, float)):
        valid_string = str(value)
    elif isinstance(value, decimal.Decimal):
        valid_string = decimal.getcontext().to_sci_string(value)
    # Time
    elif isinstance(value, (datetime, date, time)):
        format = TIME_FORMATS[type(value)]
        valid_string = value.strftime(format)
    elif isinstance(value, timedelta):
        valid_string = str(value)
    # Boolean
    elif isinstance(value, bool):
        valid_string = str(value)
    # Other
    else:
        err = TypeError(f"type of {value} is unknown as a cell value's type")
        raise ValidatorException.RuntimeError(err) from err
    return valid_string


class String(Validator):
    is_arbitraty_string = True
    cell_value_type = CellValueType.STRING
    value_type = str

    allow_punctuation: bool
    allow_digits: bool
    allow_whitespace: bool
    allow_letters: bool

    @classmethod
    @classmethod
    def matches(cls, column_cell: Cell) -> bool:
        value: str = cell_value_to_string(column_cell)
        hashed = cls.hash_column_title(value)
        return hashed in cls.hashed_known_titles

    def parse_value(self) -> str | EmptyValueType | Never:
        parsed_value: str = ''
        try:
            parsed_value = cell_value_to_string(self.cell.value)
        except TypeError as err:
            raise ValidatorException.InvalidValueError(err) from err
        except Exception as err:
            raise ValidatorException.RuntimeError(err) from err
        if len(parsed_value) == 0:
            if self.allow_empty:
                return self.EmptyValue
            raise ValidatorException.EmptyValueError
        # normalize encoding to ascii
        parsed_value = unidecode(parsed_value)
        # strip blank characters around meaningful text
        parsed_value = parsed_value.strip(string.whitespace)
        # normalize case
        parsed_value = parsed_value.upper()
        if parsed_value == '':
            if self.allow_empty:
                return self.EmptyValue
            raise ValidatorException.EmptyValueError
        if not self.allow_whitespace and ' ' in parsed_value:
            raise ValidatorException.InvalidValueError
        if not self.allow_digits and any(chr in parsed_value for chr in string.digits):
            raise ValidatorException.InvalidValueError
        if not self.allow_punctuation and any(
            chr in parsed_value for chr in string.punctuation
        ):
            raise ValidatorException.InvalidValueError
        if not self.allow_letters and any(
            chr in parsed_value for chr in string.ascii_uppercase
        ):
            raise ValidatorException.InvalidValueError
        return parsed_value

    @classmethod
    def new(
        cls: type[Self],
        /,
        known_titles: Sequence[str],
        allow_punctuation: bool = True,
        allow_digits: bool = True,
        allow_whitespace: bool = True,
        allow_letters: bool = True,
        allow_empty: bool = True,
    ) -> type[Self]:
        new_class = cls._make_creatable_class()
        return new_class.__new__(
            new_class,
            known_titles,
            allow_punctuation,
            allow_digits,
            allow_whitespace,
            allow_letters,
            allow_empty,
        )

    def __new__(
        cls: type[Self],
        /,
        known_titles: Sequence[str],
        allow_punctuation: bool,
        allow_digits: bool,
        allow_whitespace: bool,
        allow_letters: bool,
        allow_empty: bool,
    ) -> Self:
        instance = super().__new__(cls, known_titles, allow_empty)
        instance.allow_punctuation = allow_punctuation
        instance.allow_digits = allow_digits
        instance.allow_whitespace = allow_whitespace
        instance.allow_letters = allow_letters
        return instance


# endregion

# region ALTERNATIVE STRING VALIDATORS


class LetterString(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str

    @classmethod
    def new(
        cls: type[Self],
        /,
        known_titles: Sequence[str],
        allow_punctuation: bool = True,
        allow_whitespace: bool = True,
        allow_empty: bool = True,
    ) -> type[Self]:
        return super().new(
            known_titles=known_titles,
            allow_punctuation=allow_punctuation,
            allow_digits=False,
            allow_whitespace=allow_whitespace,
            allow_empty=allow_empty,
        )


class MagicNumber(str):
    _hash_trap: int = 0

    def __new__(cls, text: str):
        string_instance = super().__new__(cls, text)
        string_instance._hash_trap = hash(object())
        return string_instance

    def __hash__(self) -> int:
        return self._hash_trap


class NumericString(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str

    Infinity: MagicNumber = MagicNumber('\u221e')
    NegativeInfinity: MagicNumber = MagicNumber('\u002d\u221e')
    NaN: MagicNumber = MagicNumber('NaN')
    NegativeNaN: MagicNumber = MagicNumber('-NaN')

    def is_magic_number(self, some_str: str) -> TypeIs[MagicNumber]:
        return isinstance(some_str, MagicNumber) and (
            some_str is self.Infinity
            or some_str is self.NegativeInfinity
            or some_str is self.NaN
            or some_str is self.NegativeNaN
        )

    @classmethod
    def new(
        cls: type[Self],
        /,
        known_titles: Sequence[str],
        allow_empty: bool = True,
    ) -> type[Self]:
        return super().new(
            known_titles=known_titles,
            allow_punctuation=True,
            allow_digits=True,
            allow_whitespace=False,
            allow_empty=allow_empty,
        )

    def parse_value(self) -> str | MagicNumber | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value):
            return parsed_value
        try:
            number = decimal.Decimal(parsed_value)
            if number.is_infinite():
                return self.NegativeInfinity if number.is_signed() else self.Infinity
            if number.is_nan() or number.is_qnan() or number.is_snan():
                return self.NegativeNaN if number.is_signed() else self.NaN
        except (TypeError, ValueError) as err:
            raise ValidatorException.InvalidValueError(err) from err
        except decimal.DecimalException:
            raise ValidatorException.InvalidValueError
        else:
            return parsed_value


class IntegerString(NumericString):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str

    def parse_value(self):
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value) or self.is_magic_number(parsed_value):
            return parsed_value
        try:
            int(parsed_value)
            return parsed_value
        except (ValueError, TypeError) as err:
            raise ValidatorException.InvalidValueError(err) from err


class FloatString(NumericString):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str

    def parse_value(self):
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value) or self.is_magic_number(parsed_value):
            return parsed_value
        try:
            n = float(parsed_value)
            if math.isinf(n):
                return (
                    self.Infinity if math.copysign(1, n) > 0 else self.NegativeInfinity
                )
            if math.isnan(n):
                return self.NaN if math.copysign(1, n) > 0 else self.NegativeNaN
            return parsed_value
        except (ValueError, TypeError) as err:
            raise ValidatorException.InvalidValueError(err) from err


# endregion

# region NUMERIC VALIDATORS AND PARSERS


class Float(FloatString):
    is_arbitraty_string = False
    cell_value_type = CellValueType.FLOAT
    value_type = float

    def parse_value(self) -> float | MagicNumber | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value) or self.is_magic_number(parsed_value):
            return parsed_value
        return float(parsed_value)


class Integer(IntegerString):
    is_arbitraty_string = False
    cell_value_type = CellValueType.INT
    value_type = int

    def parse_value(self) -> int | MagicNumber | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value) or self.is_magic_number(parsed_value):
            return parsed_value
        return int(parsed_value)


# endregion

# region DATE AND/OR TIME VALIDATORS AND PARSERS

_zero_datetime = datetime.fromtimestamp(0)


class UTCDateTime(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.DATETIME
    value_type = datetime
    iso_format: str = TIME_FORMATS[datetime]
    zero_datetime: datetime = _zero_datetime
    zero_date: date = _zero_datetime.date()
    zero_time: time = _zero_datetime.time()
    zero_timedelta: timedelta = _zero_datetime - _zero_datetime

    @classmethod
    def new(
        cls: type[Self], /, known_titles: Sequence[str], allow_empty: bool = True
    ) -> type[Self]:
        return super().new(
            known_titles=known_titles,
            allow_punctuation=True,
            allow_digits=True,
            allow_whitespace=True,
            allow_empty=allow_empty,
        )

    @classmethod
    def now(cls) -> datetime:
        return datetime.now(tz=timezone.utc)

    def parse_value(self) -> datetime | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value):
            return parsed_value
        if isinstance(self.cell.value, datetime):
            return self.cell.value.replace(tzinfo=timezone.utc)
        if isinstance(self.cell.value, date):
            dttime = datetime.combine(
                self.cell.value, datetime.min.time(), tzinfo=timezone.utc
            )
            return dttime
        if isinstance(self.cell.value, time):
            iso_string = self.cell.value.replace(tzinfo=timezone.utc).isoformat()
            return datetime.fromisoformat(iso_string)
        dttime: datetime | None = None
        try:
            dttime = datetime.fromisoformat(parsed_value)
        except Exception:
            pass
        try:
            ordinal = int(parsed_value)
            dttime = datetime.fromordinal(ordinal)
        except Exception:
            pass
        try:
            timestamp = float(parsed_value)
            if not math.isfinite(timestamp):
                raise TypeError
            dttime = datetime.fromtimestamp(timestamp)
        except Exception:
            pass
        if dttime is None:
            raise ValidatorException.InvalidValueError
        return dttime.replace(tzinfo=timezone.utc)


class UTCDate(UTCDateTime):
    is_arbitraty_string = False
    cell_value_type = CellValueType.DATE
    value_type = date
    iso_format: str = TIME_FORMATS[date]

    @classmethod
    def now(cls) -> date:
        return super().now().date()

    def parse_value(self) -> date | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value):
            return parsed_value
        return parsed_value.date()


class UTCTime(UTCDateTime):
    is_arbitraty_string = False
    cell_value_type = CellValueType.TIME
    value_type = time
    iso_format: str = TIME_FORMATS[time]

    @classmethod
    def now(cls) -> time:
        return super().now().time()

    def parse_value(self) -> time | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value):
            return parsed_value
        return parsed_value.time()


class UTCTimeDelta(UTCDateTime):
    is_arbitraty_string = False
    cell_value_type = CellValueType.TIMEDELTA
    value_type = timedelta

    @classmethod
    def now(cls) -> timedelta:
        return cls.zero_timedelta

    def parse_value(self) -> timedelta | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value):
            return parsed_value
        delta = parsed_value - self.zero_datetime
        return delta


# endregion

# region OPTIONAL VALUE-BASED VALIDATORS AND PARSERS


class Option(String):
    is_arbitraty_string = False
    cell_value_type = CellValueType.STRING
    value_type = str
    options: tuple[str, ...]
    hashed_options: tuple[str, ...]

    @classmethod
    def hash_option_string(cls, text: str) -> str:
        # column_title hashing is coincidently perfect for this too
        return cls.hash_column_title(text)

    @classmethod
    def is_option(cls, text: str) -> bool:
        hashed = cls.hash_option_string(text)
        return hashed in cls.hashed_options

    @classmethod
    def new(
        cls: type[Self], /, known_titles: Sequence[str], options: Sequence[str]
    ) -> type[Self]:
        new_class = super().new(known_titles, True, True, True, True, True)
        opts = tuple(iter(options))
        new_class.options = opts
        new_class.hashed_options = tuple(cls.hash_option_string(text) for text in opts)
        return new_class

    def parse_value(self) -> str | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value):
            return parsed_value
        return parsed_value if self.is_option(parsed_value) else self.EmptyValue


class Boolean(Option):
    is_arbitraty_string = False
    cell_value_type = CellValueType.BOOL
    value_type = bool
    falsy: tuple[str, ...]
    hashed_falsy: tuple[str, ...]
    truthy: tuple[str, ...]
    hashed_truthy: tuple[str, ...]

    @classmethod
    def new(
        cls: type[Self],
        /,
        known_titles: Sequence[str],
        falsy: Sequence[str],
        truthy: Sequence[str],
    ) -> type[Self]:
        opts = tuple(itertools.chain(truthy, falsy))
        new_class = super().new(known_titles, opts)
        new_class.falsy = tuple(iter(falsy))
        new_class.hashed_falsy = tuple(cls.hash_option_string(text) for text in falsy)
        new_class.truthy = tuple(iter(truthy))
        new_class.hashed_truthy = tuple(cls.hash_option_string(text) for text in truthy)
        return new_class

    def parse_value(self) -> bool | EmptyValueType | Never:
        parsed_value = super().parse_value()
        if self.is_empty(parsed_value):
            return False
        hashed = self.hash_option_string(parsed_value)
        # self.falsy and self.truthy are contained in self.options, so if it isn't empty
        # it will always be either True of False
        return hashed in self.hashed_truthy


# endregion
