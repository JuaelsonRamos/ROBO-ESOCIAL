from __future__ import annotations

import sistema.spreadsheet as sheet

from sistema.models import (
    Cell as CellModel,
    Column,
)
from utils import INT32

import string

from abc import abstractmethod
from datetime import date, datetime
from itertools import zip_longest
from typing import Any, Sequence, TypeAlias, cast

from openpyxl.cell import Cell
from unidecode import unidecode_expect_nonascii


DefaultDict: TypeAlias = dict[str, Any]

# TODO Validator returns Row object
# TODO Validators as instances instead of static classes (to allow caching)
# TODO RowValidator object to allow conditional validation of whole rows


class CellValidationError(Exception):
    pass


class ValidatorCreationError(Exception):
    pass


class Validator:
    qualified_type: sheet.QualifiedType

    _not_inited_var_errmsg = 'propriedade não deve ser acessada antes de inicializada'

    @abstractmethod
    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel: ...


class String(Validator):
    qualified_type: sheet.QualifiedType = sheet.STRING

    __min_string_length: int | None = None
    __max_string_length: int | None = None

    @property
    def min_string_length(self) -> int:
        if self.__min_string_length is None:
            raise ValidatorCreationError(self._not_inited_var_errmsg)
        return self.__min_string_length

    @min_string_length.setter
    def min_string_length(self, value: int) -> None:
        assert isinstance(value, int)
        if self.__min_string_length is None or value < self.__min_string_length:
            self.__min_string_length = value

    @property
    def max_string_length(self) -> int:
        if self.__max_string_length is None:
            raise ValidatorCreationError(self._not_inited_var_errmsg)
        return self.__max_string_length

    @max_string_length.setter
    def max_string_length(self, value: int) -> None:
        assert isinstance(value, int)
        if self.__max_string_length is None or value > self.__max_string_length:
            self.__max_string_length = value

    def __init__(
        self,
        *,
        min_string_length: int = 1,
        max_string_length: int = INT32.MAX,
        allow_empty: bool = False,
    ):
        super().__init__()
        try:
            assert min_string_length > 0
            assert max_string_length < INT32.MAX
            assert min_string_length < max_string_length
        except AssertionError as err:
            raise ValidatorCreationError(err) from err

        self.min_string_length = min_string_length
        self.max_string_length = max_string_length
        self.allow_empty = allow_empty

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        cell_namespace: dict[str, Any] = {
            'is_arbitrary_string': True,
            'qualified_type': self.qualified_type,
            'validator': self,
        }
        try:
            assert isinstance(cell, Cell)
            assert isinstance(column, Column)
            assert isinstance(cell_index, int)
            assert isinstance(property_name, str)
            assert cell_index >= 0
            property_name = property_name.strip(string.whitespace)
            assert property_name != ''
        except AssertionError as err:
            raise CellValidationError(err) from err
        cell_namespace.update(
            index=cell_index,
            property_name=property_name,
            required=column.required,
            column_metadata=column,
            original_value=cell.value,
        )
        value = cell.value
        if value is not None:
            value = cast(str, value)
        if value != '':
            value = value.strip(string.whitespace)
        if value is None or value == '':
            cell_namespace.update(
                is_empty=True, is_valid=self.allow_empty, qualified_value=''
            )
            return CellModel(**cell_namespace)

        cell_namespace['is_empty'] = False
        try:
            assert len(value) >= self.min_string_length
            assert len(value) <= self.max_string_length
        except AssertionError:
            cell_namespace.update(is_valid=False, qualified_value='')
        else:
            cell_namespace.update(is_valid=True, qualified_value=value)

        return CellModel(**cell_namespace)


class IntegerString(String):
    def __init__(
        self,
        *,
        min_string_length: int = 1,
        max_string_length: int = INT32.MAX,
        min_integer: int = INT32.MIN,
        max_integer: int = INT32.MAX,
        allow_zero: bool = True,
        allow_empty: bool = False,
    ):
        try:
            assert min_integer >= INT32.MIN
            assert max_integer <= INT32.MAX
            assert min_integer < max_integer
        except AssertionError as err:
            raise ValidatorCreationError(err) from err

        super().__init__(
            min_string_length=min_string_length,
            max_string_length=max_string_length,
            allow_empty=allow_empty,
        )
        self.min_integer = min_integer
        self.max_integer = max_integer
        self.allow_zero = allow_zero

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        super_result = super().__call__(column, cell, cell_index, property_name)
        cell_namespace: dict[str, Any] = super_result.model_dump()
        cell_namespace['is_arbitrary_string'] = False
        if not super_result.is_valid:
            return CellModel(**cell_namespace)
        value: str = cast(str, super_result.qualified_value)
        try:
            if not super_result.is_empty:
                assert value.isdigit()
            integer = int(value)
            if not self.allow_zero:
                assert integer != 0
            assert integer >= self.min_integer
            assert integer <= self.max_integer
        except (AssertionError, TypeError):
            cell_namespace['is_valid'] = False
        else:
            cell_namespace['qualified_value'] = value
        return CellModel(**cell_namespace)


class LetterString(String):
    def __init__(
        self,
        *,
        min_string_length: int = 1,
        max_string_length: int = INT32.MAX,
        allow_empty: bool = False,
        expect_unicode: bool = False,
    ):
        super().__init__(
            min_string_length=min_string_length,
            max_string_length=max_string_length,
            allow_empty=allow_empty,
        )
        self.expect_unicode = expect_unicode

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        super_result = super().__call__(column, cell, cell_index, property_name)
        cell_namespace: dict[str, Any] = super_result.model_dump()
        cell_namespace['is_arbitrary_string'] = False
        if not super_result.is_valid or super_result.is_empty:
            return CellModel(**cell_namespace)
        value: str = cast(str, super_result.qualified_value)
        try:
            if self.expect_unicode:
                assert unidecode_expect_nonascii(value).isalpha()
            else:
                assert value.isalpha()
        except AssertionError:
            cell_namespace['is_valid'] = False
        else:
            cell_namespace['qualified_value'] = value
        return CellModel(**cell_namespace)


class Integer(IntegerString):
    qualified_type = sheet.INT

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        super_result = super().__call__(column, cell, cell_index, property_name)
        cell_namespace: dict[str, Any] = super_result.model_dump()
        value: str = cast(str, super_result.qualified_value)
        if super_result.is_valid and super_result.qualified_value != '':
            cell_namespace['qualified_value'] = int(value)
        else:
            cell_namespace['qualified_value'] = 0
        return CellModel(**cell_namespace)


class Float(String):
    qualified_type = sheet.FLOAT

    def __init__(
        self,
        *,
        min_string_length: int = 1,
        max_string_length: int = INT32.MAX,
        min_float: float = INT32.MIN.asfloat(),
        max_float: float = INT32.MAX.asfloat(),
        allow_zero: bool = True,
        allow_empty: bool = False,
    ):
        try:
            assert min_float >= INT32.MIN.asfloat()
            assert max_float <= INT32.MAX.asfloat()
            assert min_float < max_float
        except AssertionError as err:
            raise ValidatorCreationError(err) from err

        super().__init__(
            min_string_length=min_string_length,
            max_string_length=max_string_length,
            allow_empty=allow_empty,
        )
        self.min_float = min_float
        self.max_float = max_float
        self.allow_zero = allow_zero

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        super_result = super().__call__(column, cell, cell_index, property_name)
        cell_namespace: dict[str, Any] = super_result.model_dump()
        cell_namespace['is_arbitrary_string'] = False
        if not super_result.is_valid:
            return CellModel(**cell_namespace)
        value: str = cast(str, super_result.qualified_value)
        try:
            if not super_result.is_empty:
                assert value.isnumeric()
            numeric = float(value)
            if not self.allow_zero:
                assert numeric != 0
            assert numeric >= self.min_float
            assert numeric <= self.max_float
        except (AssertionError, TypeError):
            cell_namespace.update(is_valid=False, qualified_value=float(0))
        else:
            cell_namespace.update(qualified_value=numeric)
        return CellModel(**cell_namespace)


_MIN_REASONABLE_DATE = date(1970, 1, 1)
_MAX_REASONABLE_DATE = date(2100, 12, 31)
_MIN_POSSIBLE_DATE = date(1, 1, 1)


class Date(String):
    qualified_type = sheet.DATE
    min_possible_date = _MIN_POSSIBLE_DATE
    min_reasonable_date = _MIN_REASONABLE_DATE
    max_reasonable_date = _MAX_REASONABLE_DATE

    def __init__(
        self,
        *,
        min_date: date = _MIN_REASONABLE_DATE,
        max_date: date = _MAX_REASONABLE_DATE,
        allow_empty: bool = False,
    ):
        try:
            assert min_date >= self.min_reasonable_date
            assert max_date <= self.max_reasonable_date
            assert min_date < max_date
        except AssertionError as err:
            raise ValidatorCreationError(err) from err

        format_length: int = len('dd/mm/aaaa')
        super().__init__(
            min_string_length=format_length,
            max_string_length=format_length,
            allow_empty=allow_empty,
        )
        self.format_length = format_length
        self.format = '%d/%m/%Y'
        self.min_date = min_date
        self.max_date = max_date

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        super_result = super().__call__(column, cell, cell_index, property_name)
        cell_namespace: dict[str, Any] = super_result.model_dump()
        cell_namespace['is_arbitrary_string'] = False
        if not super_result.is_valid:
            return CellModel(**cell_namespace)
        value: str = cast(str, super_result.qualified_value)
        try:
            t = datetime.strptime(value, self.format).date()
            assert t >= self.min_date
            assert t <= self.max_date
        except AssertionError:
            cell_namespace.update(
                is_valid=False,
                qualified_value=self.min_possible_date,
            )
        except (TypeError, ValueError):
            cell_namespace.update(
                is_valid=self.allow_empty,
                qualified_value=self.min_possible_date,
            )
        else:
            cell_namespace.update(is_valid=True, qualified_value=t)
        return CellModel(**cell_namespace)


class Boolean(String):
    qualified_type = sheet.BOOL

    def __init__(
        self,
        *,
        falsy: Sequence[str] = [],
        truthy: Sequence[str] = [],
        case_sensitive: bool = False,
        expect_unicode: bool = False,
        allow_empty: bool = False,
    ):
        try:
            assert len(falsy) > 0
            assert len(truthy) > 0
        except AssertionError as err:
            raise ValidatorCreationError(err) from err

        self.expect_unicode = expect_unicode
        self.case_sensitive = case_sensitive
        min_string_length = INT32.MAX
        max_string_length = 0
        self.falsy, self.truthy = set(), set()
        for false, true in zip_longest(self.falsy, self.truthy):
            if false is not None:
                buffer = false
                if self.expect_unicode:
                    buffer = unidecode_expect_nonascii(buffer)
                if not self.case_sensitive:
                    buffer = buffer.lower()
                self.min_string_length = len(buffer)
                self.max_string_length = len(buffer)
                self.falsy.add(buffer)

            if true is not None:
                buffer = true
                if self.expect_unicode:
                    buffer = unidecode_expect_nonascii(buffer)
                if not self.case_sensitive:
                    buffer = buffer.lower()
                self.min_string_length = len(buffer)
                self.max_string_length = len(buffer)
                self.truthy.add(buffer)

        super().__init__(
            min_string_length=min_string_length,
            max_string_length=max_string_length,
            allow_empty=allow_empty,
        )

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        super_result = super().__call__(column, cell, cell_index, property_name)
        cell_namespace: dict[str, Any] = super_result.model_dump()
        cell_namespace['is_arbitrary_string'] = False
        if not super_result.is_valid:
            return CellModel(**cell_namespace)
        value: str = cast(str, super_result.qualified_value)
        if self.expect_unicode:
            value = unidecode_expect_nonascii(value)
        if not self.case_sensitive:
            value = value.lower()
        if value in self.truthy:
            cell_namespace['qualified_value'] = True
        elif value in self.falsy:
            cell_namespace['qualified_value'] = False
        else:
            cell_namespace['qualified_value'] = False
        return CellModel(**cell_namespace)


class Option(String):
    def __init__(
        self,
        *,
        options: Sequence[str] = [],
        case_sensitive: bool = False,
        expect_unicode: bool = False,
        allow_empty: bool = False,
    ):
        try:
            assert len(options) > 0
        except AssertionError as err:
            raise ValidatorCreationError(err) from err

        self.expect_unicode = expect_unicode
        self.case_sensitive = case_sensitive
        min_string_length = INT32.MAX
        max_string_length = 0
        self.options = set()
        for opt in options:
            buffer = opt
            if self.expect_unicode:
                buffer = unidecode_expect_nonascii(buffer)
            if not self.case_sensitive:
                buffer = buffer.lower()
            self.min_string_length = len(buffer)
            self.max_string_length = len(buffer)
            self.options.add(buffer)

        super().__init__(
            min_string_length=min_string_length,
            max_string_length=max_string_length,
            allow_empty=allow_empty,
        )

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        super_result = super().__call__(column, cell, cell_index, property_name)
        cell_namespace: dict[str, Any] = super_result.model_dump()
        cell_namespace['is_arbitrary_string'] = False
        if not super_result.is_valid or super_result.is_empty:
            return CellModel(**cell_namespace)
        value: str = cast(str, super_result.qualified_value)
        if self.expect_unicode:
            value = unidecode_expect_nonascii(value)
        if not self.case_sensitive:
            value = value.lower()
        it: Any = ...
        for opt in self.options:
            if value == opt:
                it = opt
                break
        if it is ...:
            cell_namespace['is_valid'] = False
        else:
            cell_namespace['qualified_value'] = it
        return CellModel(**cell_namespace)


class Enum(String):
    def __init__(
        self,
        *,
        enum: dict[str, Any] = {},
        case_sensitive: bool = False,
        expect_unicode: bool = False,
        allow_empty: bool = False,
    ):
        self.expect_unicode = expect_unicode
        self.case_sensitive = case_sensitive
        min_string_length = INT32.MAX
        max_string_length = 0
        self.enum = {}
        try:
            assert len(enum) > 0
            for key, value in enum.items():
                assert isinstance(key, str)
                buffer = key.strip(string.whitespace)
                assert buffer != ''
                if self.expect_unicode:
                    buffer = unidecode_expect_nonascii(buffer)
                if not self.case_sensitive:
                    buffer = buffer.lower()
                self.min_string_length = len(buffer)
                self.max_string_length = len(buffer)
                self.enum[buffer] = value
        except AssertionError as err:
            raise ValidatorCreationError(err) from err

        super().__init__(
            min_string_length=min_string_length,
            max_string_length=max_string_length,
            allow_empty=allow_empty,
        )

    def __call__(
        self, column: Column, cell: Cell, /, cell_index: int, property_name: str
    ) -> CellModel:
        super_result = super().__call__(column, cell, cell_index, property_name)
        cell_namespace: dict[str, Any] = super_result.model_dump()
        cell_namespace['is_arbitrary_string'] = False
        if not super_result.is_valid or super_result.is_empty:
            return CellModel(**cell_namespace)
        value: str = cast(str, super_result.qualified_value)
        if value not in self.enum:
            cell_namespace['is_valid'] = False
        else:
            cell_namespace['qualified_value'] = self.enum[value]
        return CellModel(**cell_namespace)
