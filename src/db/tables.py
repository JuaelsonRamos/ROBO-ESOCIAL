from __future__ import annotations

import re
import string

from typing import Any, TypeAlias

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Double,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    UnicodeText,
    func,
)


_DocstringType: TypeAlias = dict[str, dict[str, str]]


def _format_docstrings(docstrings: dict[str, str]) -> _DocstringType:
    """Formats docstrings for nomalization while keeping dictionary's keys suggestions
    and allowing for a regular python dict object's definition syntax.
    """
    converted: _DocstringType = {}
    for column_name, doc_string in docstrings.copy().items():
        formatted = re.sub(f'[{string.whitespace}]+', ' ', doc_string)
        formatted = formatted.strip(' .').title()
        converted[column_name] = {'doc': formatted, 'comment': formatted}
    return converted


_common_metadata = MetaData()

_common_docstrings: dict[str, Any] = {
    '_last_modified': 'datetime value is only non-null in case it has been modified at least once, while a creation date is always present',
}
_common_docstrings = _format_docstrings(_common_docstrings)

_common_colums = {
    '_created': Column(
        '_created',
        DateTime,
        nullable=False,
        unique=False,
        server_default=func.now(),
    ),
    '_last_modified': Column(
        '_last_modified',
        DateTime,
        nullable=True,
        unique=False,
        **_common_docstrings['_last_modified'],
        server_onupdate=func.now(),
    ),
    '_id': Column(
        '_id',
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        nullable=False,
    ),
}


def make_cookies() -> Table:
    docstrings: dict[str, Any] = {
        '_browser': 'which playwright browser does these cookies are valid for',
    }
    docstrings = _format_docstrings(docstrings)

    cookies = Table(
        'cookies',
        _common_metadata,
        _common_colums['_id'],
        Column(
            '_browser',
            Enum('firefox', 'chromium'),
            nullable=False,
            unique=False,
            **docstrings['_browser'],
        ),
        Column('name', UnicodeText(256), nullable=False, unique=False),
        Column('value', UnicodeText(2048), nullable=False, unique=False),
        Column('domain', UnicodeText(128), nullable=False, unique=False),
        Column('path', UnicodeText(256), nullable=False, unique=False),
        Column('expires', Double, nullable=False, unique=False),
        Column('httpOnly', Boolean, nullable=False, unique=False),
        Column('secure', Boolean, nullable=False, unique=False),
        Column('sameSite', Enum('Strict', 'Lax', 'None'), nullable=False, unique=False),
    )

    return cookies


def make_local_storage() -> Table:
    docstring: dict[str, Any] = {
        'name_value': """
            length of name and value are theorically infinite as long as the total storage
            taken by name=value pairs doesn't exceed 5MiB, whether thats five 1MiB pairs
            (strings), or one 5MiB pair, doesn't matter
        """
    }
    docstring = _format_docstrings(docstring)

    local_storage = Table(
        'local_storage',
        _common_metadata,
        _common_colums['_id'],
        _common_colums['_created'],
        _common_colums['_last_modified'],
        Column('_origin', ForeignKey('origins._id'), nullable=False, unique=False),
        Column(
            'name',
            UnicodeText(1024),
            nullable=False,
            unique=False,
            default='',
            **docstring['name_value'],
        ),
        Column(
            'value',
            UnicodeText(2048),
            nullable=False,
            unique=False,
            **docstring['name_value'],
        ),
    )

    return local_storage


def make_origins() -> Table:
    origins = Table(
        'origins',
        _common_metadata,
        _common_colums['_id'],
        _common_colums['_created'],
        Column('origin', UnicodeText(1024), nullable=False, unique=False),
    )

    return origins


def make_origins_localstorage() -> Table:
    docstring: dict[str, Any] = {
        'origins_localstorage': 'Association table: one origin to many local_storage',
    }
    docstring = _format_docstrings(docstring)

    origins_localstorage = Table(
        'origins_localstorage',
        _common_metadata,
        _common_colums['_id'],
        Column('origin_id', ForeignKey('origins._id'), nullable=False, unique=False),
        Column(
            'local_storage_id',
            ForeignKey('local_storage._id'),
            nullable=False,
            unique=False,
        ),
        **docstring['origins_localstorage'],
    )

    return origins_localstorage


def make_cookies_browsercontext() -> Table:
    docstring: dict[str, Any] = {
        'cookies_browsercontext': 'Association table: one browser_context to many cookies',
    }
    docstring = _format_docstrings(docstring)

    cookies_browsercontext = Table(
        'cookies_browsercontext',
        _common_metadata,
        _common_colums['_id'],
        Column(
            'browser_context_id',
            ForeignKey('browser_context._id'),
            nullable=False,
            unique=False,
        ),
        Column('cookies_id', ForeignKey('cookies._id'), nullable=False, unique=False),
        **docstring['cookies_browsercontext'],
    )

    return cookies_browsercontext


def make_origins_browsercontext() -> Table:
    docstring: dict[str, Any] = {
        'origins_browsercontext': 'Association table: one browser_context to many origins',
    }
    docstring = _format_docstrings(docstring)

    origins_browsercontext = Table(
        'origins_browsercontext',
        _common_metadata,
        _common_colums['_id'],
        Column(
            'browser_context_id',
            ForeignKey('browser_context._id'),
            nullable=False,
            unique=False,
        ),
        Column('origins_id', ForeignKey('origins._id'), nullable=False, unique=False),
        **docstring['origins_browsercontext'],
    )

    return origins_browsercontext


def make_client_certificate() -> Table:
    docstring: dict[str, Any] = {
        'browser_context_id': 'one client_certificate to many browser_contexts',
    }
    docstring = _format_docstrings(docstring)

    client_certificate = Table(
        'client_certificate',
        _common_metadata,
        _common_colums['_id'],
        _common_colums['_created'],
        _common_colums['_last_modified'],
        Column(
            'browser_context_id',
            ForeignKey('browser_context._id'),
            nullable=False,
            unique=False,
            **docstring['browser_context_id'],
        ),
        Column('origin', UnicodeText(2048), nullable=False, unique=False),
        Column('certPath', UnicodeText(2048), nullable=True, unique=True),
        Column('cert', LargeBinary(), nullable=True, unique=True),
        Column('keyPath', UnicodeText(2048), nullable=True, unique=True),
        Column('key', LargeBinary(), nullable=True, unique=True),
        Column('pfxPath', UnicodeText(2048), nullable=True, unique=True),
        Column('pfx', LargeBinary(), nullable=True, unique=True),
        Column('passphrase', UnicodeText(256), nullable=True, unique=False),
    )

    return client_certificate


def make_browser_context() -> Table:
    browser_context = Table(
        'browser_context',
        _common_metadata,
        _common_colums['_id'],
        _common_colums['_created'],
        _common_colums['_last_modified'],
        Column('accept_downloads', Boolean, nullable=False, unique=False),
        Column('offline', Boolean, nullable=False, unique=False),
        Column('javascript_enabled', Boolean, nullable=False, unique=False),
        Column('is_mobile', Boolean, nullable=False, unique=False),
        Column('has_touch', Boolean, nullable=False, unique=False),
        Column(
            'color_scheme',
            Enum('light', 'dark', 'no-preference', 'null'),
            nullable=False,
            unique=False,
        ),
        Column(
            'reduced_motion',
            Enum('reduce', 'no-preference', 'null'),
            nullable=False,
            unique=False,
        ),
        Column(
            'forced_colors',
            Enum('active', 'none', 'null'),
            nullable=False,
            unique=False,
        ),
        Column('locale', Enum('pt', 'pt-BR'), nullable=False, unique=False),
        Column(
            'timezone_id',
            Enum(
                # Simple chart of timzone identifiers at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
                # Some timezone identifiers link to others, e.g. 'America/Porto_Acre'
                # is linked to 'America/Rio_Branco'. Maybe because it's deprecated, since
                # it's listed in the 'backward' list, which I suppose stands for
                # 'Backwards Compatibility'? I didn't read through, just grabbed the values
                # because I know they are valid. I've written 'America/Recife' into a
                # couple of config files throughout time, and the timezone data has
                # always displayed correctly.
                'America/Araguaina',
                'America/Bahia',
                'America/Belem',
                'America/Boa_Vista',
                'America/Campo_Grande',
                'America/Cuiaba',
                'America/Eirunepe',
                'America/Fortaleza',
                'America/Maceio',
                'America/Manaus',
                'America/Noronha',
                'America/Porto_Velho',
                'America/Recife',
                'America/Rio_Branco',
                'America/Santarem',
                'America/Sao_Paulo',
            ),
            nullable=False,
            unique=False,
        ),
    )

    return browser_context


def make_processing_entry() -> Table:
    processing_entry = Table(
        'processing_entry',
        _common_metadata,
        _common_colums['_id'],
        _common_colums['_created'],
    )

    return processing_entry


def make_image_media() -> Table:
    docstring: dict[str, Any] = {
        'blob': 'Blobs are part of a specific processing entry but two binary blobs may be equal by pure chance',
        'timeline_index': "Index indicating it's position in the order of images created. Image 0 was the first created, and so on",
        'processing_entry_id': 'one processing_entry to many image_media',
        'action_of_origin': "action that originated the image, identical images may be originated from diferent actions by pure chance, but they wouldn't be treated differently, even if the difference could be noticed",
    }
    docstring = _format_docstrings(docstring)

    image_media = Table(
        'image_media',
        _common_metadata,
        _common_colums['_id'],
        _common_colums['_created'],
        Column(
            'blob',
            LargeBinary,
            unique=False,
            nullable=False,
            **docstring['blob'],
        ),
        Column('sha512', String(88), unique=False, nullable=False),
        Column(
            'processing_entry_id',
            ForeignKey('processing_entry._id'),
            unique=False,
            nullable=True,
            **docstring['processing_entry_id'],
        ),
        Column(
            'timeline_index',
            Integer,
            unique=False,
            nullable=False,
            **docstring['timeline_id'],
        ),
        Column('media_type', Enum('jpeg'), unique=False, nullable=False),
        Column(
            'action_of_origin',
            Enum('processing', 'preview', 'recording'),
            unique=False,
            nullable=False,
            **docstring['action_of_origin'],
        ),
        Column('size', Integer, nullable=False, unique=False),
        Column(
            'width',
            Integer,
            nullable=False,
            unique=False,
        ),
        Column(
            'height',
            Integer,
            nullable=False,
            unique=False,
        ),
    )

    return image_media


tables: dict[str, Table] = {
    'cookies': make_cookies(),
    'local_storage': make_local_storage(),
    'origins': make_origins(),
    'origins_localstorage': make_origins_localstorage(),
    'cookies_browsercontext': make_cookies_browsercontext(),
    'origins_browsercontext': make_origins_browsercontext(),
    'client_certificate': make_client_certificate(),
    'browser_context': make_browser_context(),
    'processing_entry': make_processing_entry(),
    'image_media': make_image_media(),
}
